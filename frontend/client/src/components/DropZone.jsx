import React, { useState, useCallback, useRef } from "react";
import { Upload, FileText, X } from "lucide-react";
import { cn } from "../lib/utils";
import { motion, AnimatePresence } from "framer-motion";

export default function DropZone({ onFileSelect, file, onRemove }) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef(null);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setIsDragging(false);
      const dropped = e.dataTransfer.files[0];
      if (dropped) validateAndSelect(dropped);
    },
    [onFileSelect]
  );

  const validateAndSelect = (f) => {
    const ext = f.name.split(".").pop()?.toLowerCase();
    if (!["pdf", "docx"].includes(ext)) {
      return; // silently reject — only PDF/DOCX
    }
    if (f.size > 10 * 1024 * 1024) {
      return; // max 10MB
    }
    onFileSelect(f);
  };

  const handleChange = (e) => {
    const f = e.target.files?.[0];
    if (f) validateAndSelect(f);
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-3">
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload your resume. Drag and drop or click to browse. Supports PDF and DOCX."
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        className={cn(
          "relative flex flex-col items-center justify-center gap-3",
          "p-10 rounded-2xl border-2 border-dashed cursor-pointer",
          "transition-all duration-300 ease-out",
          isDragging
            ? "border-primary-400 bg-primary-50 scale-[1.02] shadow-lg"
            : "border-slate-200 bg-white hover:border-primary-300 hover:bg-primary-50/50"
        )}
      >
        <motion.div
          animate={isDragging ? { y: -4, scale: 1.1 } : { y: 0, scale: 1 }}
          transition={{ type: "spring", stiffness: 300, damping: 20 }}
        >
          <Upload
            className={cn(
              "w-10 h-10 transition-colors",
              isDragging ? "text-primary-500" : "text-slate-300"
            )}
            aria-hidden="true"
          />
        </motion.div>
        <div className="text-center">
          <p className="text-sm font-semibold text-slate-700">
            Drag & drop your resume here
          </p>
          <p className="text-xs text-slate-400 mt-1">
            or click to browse · PDF and DOCX · Max 10 MB
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          onChange={handleChange}
          className="sr-only"
          aria-label="Upload resume file"
        />
      </div>

      <AnimatePresence>
        {file && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="flex items-center gap-3 bg-emerald-50 border border-emerald-200 rounded-2xl px-4 py-3"
          >
            <FileText className="w-5 h-5 text-emerald-600 flex-shrink-0" aria-hidden="true" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-emerald-800 truncate">
                {file.name}
              </p>
              <p className="text-xs text-emerald-600">{formatSize(file.size)}</p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemove();
              }}
              className="p-1.5 rounded-full hover:bg-emerald-100 transition-colors"
              aria-label={`Remove ${file.name}`}
            >
              <X className="w-4 h-4 text-emerald-600" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
