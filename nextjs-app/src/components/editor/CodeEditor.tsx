"use client";

import React, { useEffect, useRef, useState } from "react";
import { EditorState } from "@codemirror/state";
import { EditorView, keymap, lineNumbers, highlightActiveLineGutter, highlightSpecialChars, drawSelection, dropCursor, rectangularSelection, crosshairCursor, highlightActiveLine } from "@codemirror/view";
import { defaultKeymap, history, historyKeymap, indentWithTab } from "@codemirror/commands";
import { bracketMatching, foldGutter, foldKeymap, indentOnInput, syntaxHighlighting, defaultHighlightStyle } from "@codemirror/language";
import { oneDark } from "@codemirror/theme-one-dark";

// Languages
import { python } from "@codemirror/lang-python";
import { cpp } from "@codemirror/lang-cpp";
import { java } from "@codemirror/lang-java";
import { javascript } from "@codemirror/lang-javascript";

interface CodeEditorProps {
  value: string;
  language: string;
  onChange: (value: string) => void;
  height?: string;
  readOnly?: boolean;
}

export function CodeEditor({ value, language, onChange, height = "400px", readOnly = false }: CodeEditorProps) {
  const editorRef = useRef<HTMLDivElement>(null);
  const [view, setView] = useState<EditorView | null>(null);

  useEffect(() => {
    if (!editorRef.current) return;

    let langExtension;
    switch (language) {
      case "python":
        langExtension = python();
        break;
      case "cpp":
      case "c":
        langExtension = cpp();
        break;
      case "java":
        langExtension = java();
        break;
      case "javascript":
        langExtension = javascript();
        break;
      default:
        langExtension = python();
    }

    const state = EditorState.create({
      doc: value,
      extensions: [
        lineNumbers(),
        highlightActiveLineGutter(),
        highlightSpecialChars(),
        history(),
        foldGutter(),
        drawSelection(),
        dropCursor(),
        EditorState.allowMultipleSelections.of(true),
        indentOnInput(),
        syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
        bracketMatching(),
        rectangularSelection(),
        crosshairCursor(),
        highlightActiveLine(),
        keymap.of([
          ...defaultKeymap,
          ...historyKeymap,
          ...foldKeymap,
          indentWithTab
        ]),
        oneDark,
        langExtension,
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
            onChange(update.state.doc.toString());
          }
        }),
        EditorState.readOnly.of(readOnly),
        EditorView.theme({
          "&": {
            height: height,
          },
          ".cm-scroller": {
            overflow: "auto",
            fontFamily: "'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace",
          }
        })
      ]
    });

    const newView = new EditorView({
      state,
      parent: editorRef.current
    });

    setView(newView);

    return () => {
      newView.destroy();
    };
  }, [language, height, readOnly]); // Re-create when language changes

  // Update content if value changes externally (and not by the editor itself)
  useEffect(() => {
    if (view && value !== view.state.doc.toString()) {
      view.dispatch({
        changes: { from: 0, to: view.state.doc.length, insert: value }
      });
    }
  }, [value, view]);

  return (
    <div 
      ref={editorRef} 
      className="border border-[#2d3748] rounded-md overflow-hidden bg-[#282c34]"
      style={{ height }}
    />
  );
}
