
import { useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { ScrollArea } from "../components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "../components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import {
  Search,
  Plus,
  FolderOpen,
  FileText,
  MoreHorizontal,
  Trash2,
  LogOut,
  FolderPlus,
} from "lucide-react";

const FOLDER_COLORS = [
  "#E06A4F", "#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899"
];

const Sidebar = ({
  user,
  folders,
  notes,
  selectedFolder,
  selectedNote,
  searchQuery,
  onSelectFolder,
  onSelectNote,
  onSearchChange,
  onCreateNote,
  onCreateFolder,
  onDeleteFolder,
  onLogout,
}) => {
  const [newFolderName, setNewFolderName] = useState("");
  const [newFolderColor, setNewFolderColor] = useState(FOLDER_COLORS[0]);
  const [isCreateFolderOpen, setIsCreateFolderOpen] = useState(false);

  const handleCreateFolder = () => {
    if (newFolderName.trim()) {
      onCreateFolder(newFolderName.trim(), newFolderColor);
      setNewFolderName("");
      setNewFolderColor(FOLDER_COLORS[0]);
      setIsCreateFolderOpen(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return "Today";
    if (days === 1) return "Yesterday";
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  const getPreviewText = (content) => {
    // Strip HTML tags for preview
    const stripped = content?.replace(/<[^>]*>/g, "") || "";
    return stripped.substring(0, 60) + (stripped.length > 60 ? "..." : "");
  };

  return (
    <div className="h-full flex flex-col bg-[#F4F0EB]" data-testid="sidebar">
      {/* Header */}
      <div className="p-4 border-b border-[#E7E5E4]">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Avatar className="h-10 w-10">
              <AvatarImage src={user?.picture} alt={user?.name} />
              <AvatarFallback className="bg-[#E06A4F] text-white font-medium">
                {user?.name?.charAt(0)?.toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div>
              <p className="font-heading font-semibold text-[#1C1917] text-sm truncate max-w-[140px]">
                {user?.name}
              </p>
              <p className="text-xs text-[#A8A29E] font-body truncate max-w-[140px]">
                {user?.email}
              </p>
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8" data-testid="user-menu-button">
                <MoreHorizontal className="h-4 w-4 text-[#78716C]" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuItem onClick={onLogout} className="text-red-600" data-testid="logout-button">
                <LogOut className="h-4 w-4 mr-2" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#A8A29E]" />
          <Input
            placeholder="Search notes..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-9 bg-white border-[#E7E5E4] focus-visible:ring-[#E06A4F] rounded-lg font-body"
            data-testid="search-input"
          />
        </div>
      </div>

      {/* Folders */}
      <div className="p-4 border-b border-[#E7E5E4]">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-medium text-[#78716C] uppercase tracking-wide font-body">
            Folders
          </h3>
          <Dialog open={isCreateFolderOpen} onOpenChange={setIsCreateFolderOpen}>
            <DialogTrigger asChild>
              <Button variant="ghost" size="icon" className="h-6 w-6" data-testid="create-folder-button">
                <FolderPlus className="h-4 w-4 text-[#78716C]" />
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle className="font-heading">Create New Folder</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <Input
                  placeholder="Folder name"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  className="font-body"
                  data-testid="new-folder-name-input"
                />
                <div className="flex gap-2">
                  {FOLDER_COLORS.map((color) => (
                    <button
                      key={color}
                      onClick={() => setNewFolderColor(color)}
                      className={`w-8 h-8 rounded-full transition-transform ${
                        newFolderColor === color ? "scale-110 ring-2 ring-offset-2 ring-[#1C1917]" : ""
                      }`}
                      style={{ backgroundColor: color }}
                      data-testid={`folder-color-${color}`}
                    />
                  ))}
                </div>
                <Button
                  onClick={handleCreateFolder}
                  className="w-full bg-[#E06A4F] hover:bg-[#C95A41] text-white rounded-lg font-body"
                  data-testid="confirm-create-folder-button"
                >
                  Create Folder
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        <div className="space-y-1">
          <button
            onClick={() => onSelectFolder(null)}
            className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-colors font-body text-sm ${
              selectedFolder === null
                ? "bg-white text-[#1C1917] shadow-sm"
                : "text-[#78716C] hover:bg-white/50"
            }`}
            data-testid="all-notes-folder"
          >
            <FileText className="h-4 w-4" />
            All Notes
            <span className="ml-auto text-xs text-[#A8A29E]">{notes.length}</span>
          </button>

          {folders.map((folder) => (
            <div key={folder.folder_id} className="group relative">
              <button
                onClick={() => onSelectFolder(folder.folder_id)}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-colors font-body text-sm ${
                  selectedFolder === folder.folder_id
                    ? "bg-white text-[#1C1917] shadow-sm"
                    : "text-[#78716C] hover:bg-white/50"
                }`}
                data-testid={`folder-${folder.folder_id}`}
              >
                <FolderOpen className="h-4 w-4" style={{ color: folder.color }} />
                <span className="truncate">{folder.name}</span>
                <span className="ml-auto text-xs text-[#A8A29E]">
                  {notes.filter(n => n.folder_id === folder.folder_id).length}
                </span>
              </button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                    data-testid={`folder-menu-${folder.folder_id}`}
                  >
                    <MoreHorizontal className="h-3 w-3 text-[#78716C]" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem
                    onClick={() => onDeleteFolder(folder.folder_id)}
                    className="text-red-600"
                    data-testid={`delete-folder-${folder.folder_id}`}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete folder
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          ))}
        </div>
      </div>

      {/* Notes List */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="p-4 pb-2 flex items-center justify-between">
          <h3 className="text-xs font-medium text-[#78716C] uppercase tracking-wide font-body">
            Notes
          </h3>
          <Button
            onClick={onCreateNote}
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            data-testid="new-note-button"
          >
            <Plus className="h-4 w-4 text-[#E06A4F]" />
          </Button>
        </div>

        <ScrollArea className="flex-1 px-4 pb-4">
          {notes.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-sm text-[#A8A29E] font-body">No notes yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              {notes.map((note) => (
                <button
                  key={note.note_id}
                  onClick={() => onSelectNote(note)}
                  className={`w-full text-left p-3 rounded-lg transition-all duration-200 ${
                    selectedNote?.note_id === note.note_id
                      ? "bg-white shadow-sm border border-[#E7E5E4]"
                      : "hover:bg-white/50"
                  }`}
                  data-testid={`note-${note.note_id}`}
                >
                  <h4 className="font-heading font-medium text-[#1C1917] text-sm truncate mb-1">
                    {note.title || "Untitled"}
                  </h4>
                  <p className="text-xs text-[#A8A29E] font-body truncate mb-1">
                    {getPreviewText(note.content) || "No content"}
                  </p>
                  <p className="text-xs text-[#A8A29E] font-body">
                    {formatDate(note.updated_at)}
                  </p>
                </button>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>
    </div>
  );
};

export default Sidebar;