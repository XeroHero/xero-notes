
import { useState, useEffect, useCallback } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Highlight from "@tiptap/extension-highlight";
import Placeholder from "@tiptap/extension-placeholder";
import CodeBlockLowlight from "@tiptap/extension-code-block-lowlight";
import Link from "@tiptap/extension-link";
import { common, createLowlight } from "lowlight";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import {
  Bold,
  Italic,
  Underline as UnderlineIcon,
  Strikethrough,
  Highlighter,
  List,
  ListOrdered,
  Code,
  Quote,
  Heading1,
  Heading2,
  Heading3,
  Link as LinkIcon,
  MoreVertical,
  Trash2,
  Share2,
  FolderOpen,
  Save,
} from "lucide-react";
import { toast } from "sonner";
import debounce from "../utils/debounce";

// Create lowlight instance with common languages
const lowlight = createLowlight(common);

const NoteEditor = ({ note, folders, onUpdate, onDelete, onShare }) => {
  const [title, setTitle] = useState(note?.title || "");
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState(null);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        codeBlock: false,
        link: false, // Disable default link extension
      }),
      Link.configure({
        openOnClick: false, // Don't handle clicks automatically
        HTMLAttributes: {
          target: '_blank', // Open in new tab
          rel: 'noopener noreferrer',
        },
      }),
      Highlight.configure({ multicolor: true }),
      Placeholder.configure({
        placeholder: "Start writing your note...",
      }),
      CodeBlockLowlight.configure({
        lowlight,
        HTMLAttributes: {
          class: "bg-[#1C1917] rounded-lg p-4 text-sm font-mono overflow-x-auto",
        },
      }),
    ],
    content: note?.content || "",
    editorProps: {
      attributes: {
        class: "prose prose-stone max-w-none focus:outline-none min-h-[300px] font-body leading-relaxed",
      },
    },
    onUpdate: ({ editor }) => {
      if (note.note_id) {
        debouncedSave(note.note_id, { content: editor.getHTML() });
      }
    },
  });

  // Update editor content when note changes
  useEffect(() => {
    if (editor && note) {
      setTitle(note.title || "");
      if (editor.getHTML() !== note.content) {
        editor.commands.setContent(note.content || "");
      }
    }
  }, [note?.note_id]);

  // Debounced save function
  const debouncedSave = useCallback(
    debounce(async (noteId, data) => {
      if (!noteId) {
        console.error('Cannot save note: noteId is undefined');
        return;
      }
      setIsSaving(true);
      try {
        await onUpdate(noteId, data);
        setLastSaved(new Date());
      } finally {
        setIsSaving(false);
      }
    }, 1000),
    [onUpdate]
  );

  // Handle title change
  const handleTitleChange = (e) => {
    const newTitle = e.target.value;
    setTitle(newTitle);
    if (note.note_id) {
      debouncedSave(note.note_id, { title: newTitle });
    }
  };

  // Handle folder change
  const handleFolderChange = (folderId) => {
    if (note.note_id) {
      onUpdate(note.note_id, { folder_id: folderId === "none" ? null : folderId });
      toast.success("Note moved");
    }
  };

  // Handle delete
  const handleDelete = () => {
    if (note.note_id) {
      if (window.confirm("Are you sure you want to delete this note?")) {
        onDelete(note.note_id);
      }
    }
  };

  // Handle share
  const handleShare = () => {
    if (note.note_id) {
      onShare(note.note_id);
    }
  };

  // Add link
  const addLink = () => {
    const url = window.prompt("Enter URL:");
    if (url) {
      editor?.chain().focus().setLink({ href: url }).run();
    }
  };

  if (!editor) {
    return null;
  }

  return (
    <div className="h-full flex flex-col bg-white" data-testid="note-editor">
      {/* Toolbar */}
      <div className="border-b border-[#E7E5E4] px-4 py-2 flex items-center justify-between gap-2 flex-wrap">
        {/* Formatting buttons */}
        <div className="flex items-center gap-1 flex-wrap">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => editor.chain().focus().toggleBold().run()}
            className={editor.isActive("bold") ? "bg-[#F4F0EB]" : ""}
            data-testid="bold-button"
          >
            <Bold className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => editor.chain().focus().toggleItalic().run()}
            className={editor.isActive("italic") ? "bg-[#F4F0EB]" : ""}
            data-testid="italic-button"
          >
            <Italic className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => editor.chain().focus().toggleUnderline().run()}
            className={editor.isActive("underline") ? "bg-[#F4F0EB]" : ""}
            data-testid="underline-button"
          >
            <UnderlineIcon className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => editor.chain().focus().toggleStrike().run()}
            className={editor.isActive("strike") ? "bg-[#F4F0EB]" : ""}
            data-testid="strike-button"
          >
            <Strikethrough className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => editor.chain().focus().toggleHighlight().run()}
            className={editor.isActive("highlight") ? "bg-[#F4F0EB]" : ""}
            data-testid="highlight-button"
          >
            <Highlighter className="h-4 w-4" />
          </Button>

          <div className="w-px h-6 bg-[#E7E5E4] mx-1" />

          <Button
            variant="ghost"
            size="icon"
            onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
            className={editor.isActive("heading", { level: 1 }) ? "bg-[#F4F0EB]" : ""}
            data-testid="h1-button"
          >
            <Heading1 className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
            className={editor.isActive("heading", { level: 2 }) ? "bg-[#F4F0EB]" : ""}
            data-testid="h2-button"
          >
            <Heading2 className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
            className={editor.isActive("heading", { level: 3 }) ? "bg-[#F4F0EB]" : ""}
            data-testid="h3-button"
          >
            <Heading3 className="h-4 w-4" />
          </Button>

          <div className="w-px h-6 bg-[#E7E5E4] mx-1" />

          <Button
            variant="ghost"
            size="icon"
            onClick={() => editor.chain().focus().toggleBulletList().run()}
            className={editor.isActive("bulletList") ? "bg-[#F4F0EB]" : ""}
            data-testid="bullet-list-button"
          >
            <List className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
            className={editor.isActive("orderedList") ? "bg-[#F4F0EB]" : ""}
            data-testid="ordered-list-button"
          >
            <ListOrdered className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => editor.chain().focus().toggleBlockquote().run()}
            className={editor.isActive("blockquote") ? "bg-[#F4F0EB]" : ""}
            data-testid="blockquote-button"
          >
            <Quote className="h-4 w-4" />
          </Button>

          <div className="w-px h-6 bg-[#E7E5E4] mx-1" />

          <Button
            variant="ghost"
            size="icon"
            onClick={() => editor.chain().focus().toggleCodeBlock().run()}
            className={editor.isActive("codeBlock") ? "bg-[#F4F0EB]" : ""}
            data-testid="code-block-button"
          >
            <Code className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={addLink}
            className={editor.isActive("link") ? "bg-[#F4F0EB]" : ""}
            data-testid="link-button"
          >
            <LinkIcon className="h-4 w-4" />
          </Button>
        </div>

        {/* Right side actions */}
        <div className="flex items-center gap-2">
          {/* Save status */}
          <span className="text-xs text-[#A8A29E] font-body hidden sm:inline">
            {isSaving ? (
              <span className="flex items-center gap-1">
                <Save className="h-3 w-3 animate-pulse" />
                Saving...
              </span>
            ) : lastSaved ? (
              `Saved ${lastSaved.toLocaleTimeString()}`
            ) : (
              ""
            )}
          </span>

          {/* Folder selector */}
          <Select
            value={note.folder_id || "none"}
            onValueChange={handleFolderChange}
          >
            <SelectTrigger className="w-[140px] h-8 text-xs" data-testid="folder-select">
              <FolderOpen className="h-3 w-3 mr-1" />
              <SelectValue placeholder="No folder" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">No folder</SelectItem>
              {folders.map((folder) => (
                <SelectItem key={folder.folder_id} value={folder.folder_id}>
                  <span className="flex items-center gap-2">
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: folder.color }}
                    />
                    {folder.name}
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* More actions */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" data-testid="note-menu-button">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={handleShare} data-testid="share-note-button">
                <Share2 className="h-4 w-4 mr-2" />
                Share note
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={handleDelete}
                className="text-red-600"
                data-testid="delete-note-button"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete note
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Title Input */}
      <div className="px-8 pt-8 pb-4">
        <Input
          value={title}
          onChange={handleTitleChange}
          placeholder="Note title"
          className="text-3xl md:text-4xl font-heading font-semibold text-[#1C1917] border-none p-0 h-auto focus-visible:ring-0 placeholder:text-[#A8A29E] tracking-tight"
          data-testid="note-title-input"
        />
      </div>

      {/* Editor */}
      <div className="flex-1 px-8 pb-8 overflow-auto">
        <EditorContent editor={editor} data-testid="note-content-editor" />
      </div>
    </div>
  );
};

export default NoteEditor;