import {
  FileImage,
  FileText,
  FileType,
  LoaderCircle,
  Trash2,
  UploadCloud,
} from "lucide-react";
import { useMemo, useState } from "react";
import { useDropzone } from "react-dropzone";
import api from "../services/api";
import { useAppContext } from "../context/useAppContext";

function formatFileSize(size = 0) {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(2)} MB`;
}

function getDocTypeInfo(fileName = "") {
  const name = fileName.toLowerCase();
  if (name.endsWith(".pdf")) {
    return { label: "PDF", icon: FileType, className: "text-pink-300" };
  }
  if (name.endsWith(".doc") || name.endsWith(".docx")) {
    return { label: "DOCX", icon: FileText, className: "text-cyan-300" };
  }
  return { label: "Image", icon: FileImage, className: "text-purple-300" };
}

function normalizeDocuments(payload) {
  const raw = payload?.documents ?? payload?.items ?? payload ?? [];
  if (!Array.isArray(raw)) {
    return [];
  }
  return raw;
}

export default function DocumentUpload() {
  const { student, documents, setDocuments, loadDocuments, loading } =
    useAppContext();
  const [title, setTitle] = useState("");
  const [subject, setSubject] = useState("");
  const [topic, setTopic] = useState("");
  const [filesToUpload, setFilesToUpload] = useState([]);
  const [progressById, setProgressById] = useState({});
  const [uploading, setUploading] = useState(false);

  const acceptedFiles = useMemo(
    () => ({
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        [".docx"],
      "image/png": [".png"],
      "image/jpeg": [".jpg", ".jpeg"],
      "image/webp": [".webp"],
    }),
    [],
  );

  const onDrop = (accepted) => {
    const prepared = accepted.map((file) => ({
      id: `${file.name}-${file.lastModified}-${Math.random().toString(36).slice(2, 7)}`,
      file,
    }));
    setFilesToUpload((previous) => [...previous, ...prepared]);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedFiles,
    multiple: true,
  });

  const handleUploadAll = async () => {
    if (!student?.id || filesToUpload.length === 0 || uploading) {
      return;
    }

    setUploading(true);

    try {
      for (const item of filesToUpload) {
        const formData = new FormData();
        formData.append("file", item.file);
        formData.append("student_id", student.id);
        if (title.trim()) {
          formData.append("title", title.trim());
        }
        if (subject.trim()) {
          formData.append("subject", subject.trim());
        }
        if (topic.trim()) {
          formData.append("topic", topic.trim());
        }

        await api.uploadDocument(formData, (event) => {
          const total = event.total || item.file.size;
          const percent =
            total > 0 ? Math.round((event.loaded / total) * 100) : 0;
          setProgressById((previous) => ({ ...previous, [item.id]: percent }));
        });
      }

      setFilesToUpload([]);
      setProgressById({});
      setTitle("");
      setSubject("");
      setTopic("");

      const latest = await api.getDocuments(student.id);
      setDocuments(normalizeDocuments(latest));
      await loadDocuments(student.id);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (doc) => {
    const docId = doc?.id ?? doc?.document_id;
    if (!docId) {
      return;
    }

    const shouldDelete = window.confirm("Delete this document permanently?");
    if (!shouldDelete) {
      return;
    }

    await api.deleteDocument(docId);
    const latest = await api.getDocuments(student.id);
    setDocuments(normalizeDocuments(latest));
  };

  return (
    <section className="glass-panel p-4 md:p-5 animate-fade-in flex flex-col gap-5">
      <header className="border-b border-white/10 pb-3">
        <p className="text-xs uppercase tracking-[0.14em] text-slate-400">
          Knowledge Base
        </p>
        <h3 className="text-lg font-semibold hologram-text">
          Document Management
        </h3>
      </header>

      <div className="card space-y-3">
        <h4 className="text-sm font-semibold text-slate-100">
          Upload Documents
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
          <input
            className="input-field"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Optional title"
          />
          <input
            className="input-field"
            value={subject}
            onChange={(event) => setSubject(event.target.value)}
            placeholder="Optional subject"
          />
          <input
            className="input-field"
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="Optional topic"
          />
        </div>

        <div
          {...getRootProps()}
          className={`rounded-2xl border-2 border-dashed p-6 text-center transition-colors cursor-pointer ${
            isDragActive
              ? "border-cyan-300/70 bg-cyan-500/10"
              : "border-white/20 hover:border-cyan-300/50"
          }`}
        >
          <input {...getInputProps()} />
          <UploadCloud className="mx-auto mb-2 text-cyan-200" size={24} />
          <p className="text-sm text-slate-200">
            {isDragActive
              ? "Drop files here..."
              : "Drag and drop PDF, DOCX, or image files here"}
          </p>
          <p className="text-xs text-slate-400 mt-1">or click to browse</p>
        </div>

        {filesToUpload.length > 0 ? (
          <div className="space-y-2">
            {filesToUpload.map((item) => (
              <div
                key={item.id}
                className="rounded-xl border border-white/12 bg-slate-950/45 px-3 py-2"
              >
                <div className="flex items-center justify-between gap-3 text-sm">
                  <span className="text-slate-200 truncate">
                    {item.file.name}
                  </span>
                  <span className="text-slate-400 shrink-0">
                    {progressById[item.id] ?? 0}%
                  </span>
                </div>
                <div className="h-1.5 rounded-full bg-slate-800 mt-2 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 transition-all"
                    style={{ width: `${progressById[item.id] ?? 0}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : null}

        <button
          type="button"
          className="btn-primary"
          onClick={handleUploadAll}
          disabled={filesToUpload.length === 0 || uploading}
        >
          {uploading ? (
            <LoaderCircle size={16} className="animate-spin" />
          ) : (
            <UploadCloud size={16} />
          )}
          {uploading ? "Uploading..." : "Upload Selected"}
        </button>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-slate-100">
            Uploaded Documents
          </h4>
          <span className="badge badge-cyan">{documents.length} files</span>
        </div>

        {loading.documents ? (
          <div className="card flex items-center gap-2 text-slate-300">
            <LoaderCircle size={16} className="animate-spin" /> Loading
            documents...
          </div>
        ) : documents.length === 0 ? (
          <div className="card text-center py-8">
            <p className="text-slate-300">No documents uploaded yet.</p>
            <p className="text-xs text-slate-400 mt-1">
              Upload files to build your personalized learning context.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {documents.map((doc, index) => {
              const name =
                doc?.filename ||
                doc?.name ||
                doc?.title ||
                `Document ${index + 1}`;
              const info = getDocTypeInfo(name);
              const Icon = info.icon;
              const docId = doc?.id ?? doc?.document_id ?? `doc-${index}`;
              const status = (doc?.status || "ready").toString().toLowerCase();

              return (
                <article key={docId} className="card">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex gap-3 min-w-0">
                      <div
                        className={`h-10 w-10 rounded-xl border border-white/10 bg-slate-900/60 flex items-center justify-center ${info.className}`}
                      >
                        <Icon size={18} />
                      </div>
                      <div className="min-w-0">
                        <h5 className="text-sm font-semibold text-slate-100 truncate">
                          {doc?.title || name}
                        </h5>
                        <p className="text-xs text-slate-400 truncate">
                          {name}
                        </p>
                      </div>
                    </div>

                    <button
                      type="button"
                      className="btn-ghost px-2.5 py-1.5 text-xs"
                      onClick={() => handleDelete(doc)}
                    >
                      <Trash2 size={14} /> Delete
                    </button>
                  </div>

                  <div className="mt-3 flex flex-wrap gap-1.5">
                    <span className="badge badge-purple">{info.label}</span>
                    {doc?.subject ? (
                      <span className="badge badge-cyan">{doc.subject}</span>
                    ) : null}
                    {doc?.topic ? (
                      <span className="badge badge-pink">{doc.topic}</span>
                    ) : null}
                    <span className="badge badge-cyan">
                      {formatFileSize(doc?.file_size || doc?.size || 0)}
                    </span>
                    <span
                      className={`badge ${status === "ready" ? "badge-cyan" : "badge-purple"}`}
                    >
                      {status === "ready" ? "Ready" : "Processing"}
                    </span>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
