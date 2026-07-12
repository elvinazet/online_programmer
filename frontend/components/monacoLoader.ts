// Monaco грузится со своего origin (public/monaco/vs), а не с CDN jsdelivr —
// редактор кода работает в любой сети. Файлы кладёт scripts/copy-editor-assets.mjs.
// Импортируется как side-effect до монтирования редактора.
import { loader } from "@monaco-editor/react";

loader.config({ paths: { vs: "/monaco/vs" } });
