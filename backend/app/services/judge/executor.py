"""Исполнители кода: DockerExecutor (прод) и LocalExecutor (dev/тесты).

Оба дают одинаковый интерфейс: executor.session(language, source) → сессия
с методами compile() и run(stdin, time_limit_ms, memory_limit_mb).
"""
import base64
import os
import resource
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass

from app.core.config import settings
from app.models.submission import SubmissionLanguage

# Ограничение объёма вывода пользовательского кода (защита от «бомб» вывода).
MAX_OUTPUT_BYTES = 1_000_000


@dataclass
class CompileResult:
    ok: bool
    message: str = ""


@dataclass
class RunResult:
    stdout: str
    exit_code: int
    time_ms: int
    timed_out: bool = False
    oom: bool = False


# --------------------------- Local (subprocess) ---------------------------
class LocalSession:
    """Запуск через локальные процессы с ulimit. Менее изолирован — только dev/тесты."""

    def __init__(self, language: SubmissionLanguage, source_code: str):
        self.language = language
        self.workdir = tempfile.mkdtemp(prefix="judge_")
        self.binary: str | None = None
        filename = "main.py" if language == SubmissionLanguage.python else "main.cpp"
        self.src = os.path.join(self.workdir, filename)
        with open(self.src, "w", encoding="utf-8") as f:
            f.write(source_code)

    def compile(self) -> CompileResult:
        if self.language == SubmissionLanguage.python:
            proc = subprocess.run(
                ["python3", "-m", "py_compile", self.src],
                capture_output=True, text=True,
            )
            return CompileResult(proc.returncode == 0, proc.stderr[:4000])
        self.binary = os.path.join(self.workdir, "prog")
        proc = subprocess.run(
            ["g++", "-O2", "-std=c++17", "-o", self.binary, self.src],
            capture_output=True, text=True, timeout=30,
        )
        return CompileResult(proc.returncode == 0, proc.stderr[:4000])

    def _command(self) -> list[str]:
        if self.language == SubmissionLanguage.python:
            return ["python3", self.src]
        return [self.binary or ""]

    def run(self, stdin: str, time_limit_ms: int, memory_limit_mb: int) -> RunResult:
        is_cpp = self.language == SubmissionLanguage.cpp

        def set_limits():
            # CPU-лимит как backstop ставим выше wall-таймаута, чтобы TLE
            # ловился по wall-времени (иначе SIGXCPU классифицируется как RE).
            cpu = time_limit_ms // 1000 + 2
            resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
            # RLIMIT_AS ломает старт интерпретатора Python, поэтому только для C++
            if is_cpp:
                mem = memory_limit_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (mem, mem))

        start = time.monotonic()
        try:
            proc = subprocess.run(
                self._command(),
                input=stdin,
                capture_output=True,
                text=True,
                timeout=time_limit_ms / 1000 + 1,
                preexec_fn=set_limits,
            )
        except subprocess.TimeoutExpired:
            return RunResult(stdout="", exit_code=-1, time_ms=time_limit_ms, timed_out=True)
        elapsed = int((time.monotonic() - start) * 1000)
        return RunResult(
            stdout=(proc.stdout or "")[:MAX_OUTPUT_BYTES],
            exit_code=proc.returncode,
            time_ms=elapsed,
        )

    def close(self):
        shutil.rmtree(self.workdir, ignore_errors=True)


class LocalExecutor:
    def session(self, language: SubmissionLanguage, source_code: str) -> LocalSession:
        return LocalSession(language, source_code)


# --------------------------- Docker (изолированно) ---------------------------
class DockerSession:
    """Запуск в эфемерном контейнере: net=none, лимиты, без монтирования ФС хоста.

    Исходник передаётся через env SRC_B64; тест — на stdin. Контейнерный
    entrypoint компилирует (для C++) и запускает; при ошибке компиляции —
    выход с кодом 2 и маркером __COMPILE_ERROR__.
    """

    def __init__(self, language: SubmissionLanguage, source_code: str):
        self.language = language
        self.source_b64 = base64.b64encode(source_code.encode("utf-8")).decode("ascii")
        self.image = (
            settings.sandbox_image_python
            if language == SubmissionLanguage.python
            else settings.sandbox_image_cpp
        )

    def _docker_run(self, mode: str, stdin: str, time_limit_ms: int, memory_limit_mb: int):
        secs = max(1, time_limit_ms // 1000 + 1)
        cmd = [
            "docker", "run", "--rm", "-i",
            "--network", "none",
            "--cpus", "1",
            f"--memory={memory_limit_mb}m",
            "--pids-limit", "64",
            "--read-only",
            "--tmpfs", "/work:size=64m,exec,mode=1777",
            "-w", "/work",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "-e", f"SRC_B64={self.source_b64}",
            "-e", f"MODE={mode}",
            "-e", f"TIME_LIMIT={secs}",
            self.image,
        ]
        return subprocess.run(
            cmd, input=stdin, capture_output=True, text=True, timeout=secs + 8
        )

    def compile(self) -> CompileResult:
        try:
            proc = self._docker_run("compile", "", settings.judge_default_time_limit_ms, 256)
        except subprocess.TimeoutExpired:
            return CompileResult(False, "Таймаут компиляции")
        if proc.returncode == 2 or "__COMPILE_ERROR__" in proc.stderr:
            return CompileResult(False, proc.stderr.replace("__COMPILE_ERROR__", "")[:4000])
        return CompileResult(True)

    def run(self, stdin: str, time_limit_ms: int, memory_limit_mb: int) -> RunResult:
        start = time.monotonic()
        try:
            proc = self._docker_run("run", stdin, time_limit_ms, memory_limit_mb)
        except subprocess.TimeoutExpired:
            return RunResult(stdout="", exit_code=-1, time_ms=time_limit_ms, timed_out=True)
        elapsed = int((time.monotonic() - start) * 1000)
        # 137 = OOM-kill контейнера, 124 = timeout(1) внутри
        if proc.returncode == 137:
            return RunResult("", 137, elapsed, oom=True)
        if proc.returncode == 124:
            return RunResult("", 124, elapsed, timed_out=True)
        return RunResult(stdout=proc.stdout, exit_code=proc.returncode, time_ms=elapsed)

    def close(self):
        pass


class DockerExecutor:
    def session(self, language: SubmissionLanguage, source_code: str) -> DockerSession:
        return DockerSession(language, source_code)


def get_executor():
    if settings.judge_backend == "local":
        return LocalExecutor()
    return DockerExecutor()
