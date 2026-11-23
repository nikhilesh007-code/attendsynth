"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  if (!content) return null;

  return (
    <div className="prose prose-invert max-w-none text-xs leading-relaxed text-slate-300">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ ...props }) => (
            <h1 className="text-base font-bold text-white mt-4 mb-2 pb-1 border-b border-slate-800" {...props} />
          ),
          h2: ({ ...props }) => (
            <h2 className="text-sm font-bold text-white mt-3.5 mb-2" {...props} />
          ),
          h3: ({ ...props }) => (
            <h3 className="text-xs font-semibold uppercase tracking-wider text-indigo-300 mt-3 mb-1.5" {...props} />
          ),
          h4: ({ ...props }) => (
            <h4 className="text-xs font-semibold text-slate-200 mt-2 mb-1" {...props} />
          ),
          p: ({ ...props }) => (
            <p className="text-xs text-slate-300 leading-relaxed mb-2" {...props} />
          ),
          ul: ({ ...props }) => (
            <ul className="list-disc list-outside pl-4 space-y-1 mb-2 text-xs text-slate-300" {...props} />
          ),
          ol: ({ ...props }) => (
            <ol className="list-decimal list-outside pl-4 space-y-1 mb-2 text-xs text-slate-300" {...props} />
          ),
          li: ({ ...props }) => (
            <li className="text-xs text-slate-300 pl-1" {...props} />
          ),
          strong: ({ ...props }) => (
            <strong className="font-semibold text-white" {...props} />
          ),
          blockquote: ({ ...props }) => (
            <blockquote className="border-l-2 border-indigo-500 pl-3 py-1.5 my-2.5 bg-indigo-500/5 text-slate-300 rounded-r text-[11.5px]" {...props} />
          ),
          code: ({ ...props }: any) => {
            const isInline = !props.className;
            return isInline ? (
              <code className="bg-slate-800 text-indigo-300 px-1 py-0.5 rounded text-[11px] font-mono" {...props} />
            ) : (
              <pre className="bg-slate-900 border border-slate-800 p-3 rounded-lg overflow-x-auto text-[11px] font-mono my-2.5 text-slate-200">
                <code {...props} />
              </pre>
            );
          },
          table: ({ ...props }) => (
            <div className="overflow-x-auto my-3 border border-slate-800 rounded-lg">
              <table className="w-full text-xs text-left" {...props} />
            </div>
          ),
          thead: ({ ...props }) => (
            <thead className="bg-[#090d16] text-slate-300 border-b border-slate-800 font-semibold" {...props} />
          ),
          th: ({ ...props }) => (
            <th className="px-3 py-2 text-slate-200 border-b border-slate-700 font-semibold" {...props} />
          ),
          td: ({ ...props }) => (
            <td className="px-3 py-2 border-b border-slate-800/60 text-slate-300" {...props} />
          ),
          hr: ({ ...props }) => (
            <hr className="my-3 border-slate-800" {...props} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
