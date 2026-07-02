export type Role = "student" | "teacher";
export type Language = "cpp" | "python";
export type ProgressStatus = "not_started" | "in_progress" | "completed";
export type QuestionType =
  | "single_choice"
  | "multiple_choice"
  | "short_answer"
  | "code_output";

export interface User {
  id: number;
  email: string;
  role: Role;
  email_verified: boolean;
  student_profile?: {
    avatar_url?: string | null;
    codeforces_handle?: string | null;
    streak_count: number;
  } | null;
  teacher_profile?: {
    display_name?: string | null;
    bio?: string | null;
    avatar_url?: string | null;
  } | null;
}

export interface Course {
  id: number;
  title: string;
  language: Language;
  description?: string | null;
}

export interface LessonNode {
  id: number;
  title: string;
  order_index: number;
  status: ProgressStatus | null;
}
export interface ModuleNode {
  id: number;
  title: string;
  order_index: number;
  lessons: LessonNode[];
}
export interface LevelNode {
  id: number;
  name: string;
  order_index: number;
  modules: ModuleNode[];
}
export interface CourseTree extends Course {
  levels: LevelNode[];
}

export interface PublicQuestion {
  id: number;
  type: QuestionType;
  prompt_md: string;
  options?: string[] | null;
}

export interface LessonDetail {
  id: number;
  module_id: number;
  title: string;
  content_md: string;
  questions: PublicQuestion[];
  progress?: { status: ProgressStatus; quiz_score?: number | null } | null;
}

export interface QuizResultItem {
  question_id: number;
  is_correct: boolean;
  correct_answer: Record<string, unknown>;
  explanation_md?: string | null;
}
export interface QuizResult {
  score: number;
  passed: boolean;
  status: ProgressStatus;
  results: QuizResultItem[];
}

export type SubmissionStatus =
  | "queued"
  | "running"
  | "accepted"
  | "wrong_answer"
  | "tle"
  | "mle"
  | "runtime_error"
  | "compile_error";

export interface Problem {
  id: number;
  source: "codeforces" | "authored";
  title: string;
  rating?: number | null;
  url?: string | null;
  cf_contest_id?: number | null;
  cf_index?: string | null;
  tags: string[];
  solved: boolean;
}

export interface SampleTest {
  input: string;
  expected_output: string;
}

export interface ProblemDetail extends Problem {
  statement_md?: string | null;
  time_limit_ms: number;
  memory_limit_mb: number;
  samples: SampleTest[];
}

export interface Submission {
  id: number;
  problem_id: number;
  language: "cpp" | "python";
  status: SubmissionStatus;
  passed_tests: number;
  total_tests: number;
  score: number;
  time_ms?: number | null;
  compile_output?: string | null;
  created_at: string;
}

export interface Stats {
  solved_total: number;
  by_rating: Record<string, number>;
  by_tag: Record<string, number>;
}
