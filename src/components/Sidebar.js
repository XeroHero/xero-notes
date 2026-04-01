
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
    <div className="h-full flex flex-col bg-gradient-to-br from-[#FDF8F5] to-[#F4F0EB]" data-testid="sidebar">
      {/* Header */}
      <div className="p-5 border-b border-[#E7E5E4]/60">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-[#E06A4F]/20 rounded-full blur-md"></div>
              <Avatar className="h-11 w-11 relative z-10 ring-2 ring-white shadow-lg">
                <AvatarImage src={user?.picture} alt={user?.name} />
                <AvatarFallback className="bg-gradient-to-br from-[#E06A4F] to-[#C95A41] text-white font-semibold">
                  {user?.name?.charAt(0)?.toUpperCase()}
                </AvatarFallback>
              </Avatar>
            </div>
            <div className="min-w-0">
              <p className="font-heading font-semibold text-[#1C1917] text-sm truncate max-w-[150px]">
                {user?.name}
              </p>
              <p className="text-xs text-[#A8A29E] font-body truncate max-w-[150px]">
                {user?.email}
              </p>
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-9 w-9 hover:bg-white/60" data-testid="user-menu-button">
                <MoreHorizontal className="h-4 w-4 text-[#78716C]" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48 backdrop-blur-xl">
              <DropdownMenuItem onClick={onLogout} className="text-red-600" data-testid="logout-button">
                <LogOut className="h-4 w-4 mr-2" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Search */}
        <div className="relative group">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#A8A29E] group-focus-within:text-[#E06A4F] transition-colors" />
          <Input
            placeholder="Search notes..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-9 bg-white/70 backdrop-blur-sm border-[#E7E5E4]/60 focus-visible:ring-[#E06A4F]/20 focus-visible:border-[#E06A4F]/60 rounded-xl font-body transition-all duration-300 hover:bg-white/90"
            data-testid="search-input"
          />
        </div>
      </div>

      {/* Folders */}
      <div className="p-5 border-b border-[#E7E5E4]/60">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-semibold text-[#78716C] uppercase tracking-wider font-body">
            Folders
          </h3>
          <Dialog open={isCreateFolderOpen} onOpenChange={setIsCreateFolderOpen}>
            <DialogTrigger asChild>
              <Button variant="ghost" size="icon" className="h-7 w-7 hover:bg-white/60" data-testid="create-folder-button">
                <FolderPlus className="h-4 w-4 text-[#E06A4F]" />
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md backdrop-blur-xl bg-white/95">
              <DialogHeader>
                <DialogTitle className="font-heading text-lg">Create New Folder</DialogTitle>
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
                  className="w-full bg-gradient-to-r from-[#E06A4F] to-[#C95A41] hover:from-[#C95A41] hover:to-[#E06A4F] text-white rounded-xl font-body shadow-lg shadow-[#E06A4F]/30 transition-all duration-300"
                  data-testid="confirm-create-folder-button"
                >
                  Create Folder
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        <div className="space-y-1.5">
          <button
            onClick={() => onSelectFolder(null)}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl transition-all duration-200 font-body text-sm group ${
              selectedFolder === null
                ? "bg-gradient-to-r from-[#E06A4F]/10 to-[#E06A4F]/5 text-[#1C1917] shadow-md shadow-[#E7E5E4]/30"
                : "text-[#78716C] hover:bg-white/60"
            }`}
            data-testid="all-notes-folder"
          >
            <FileText className={`h-4 w-4 transition-colors ${selectedFolder === null ? 'text-[#E06A4F]' : 'text-[#A8A29E] group-hover:text-[#E06A4F]'}`} />
            <span className="font-medium">All Notes</span>
            <span className={`ml-auto text-xs font-medium px-2 py-0.5 rounded-full ${
              selectedFolder === null ? 'bg-[#E06A4F] text-white' : 'bg-[#E7E5E4] text-[#A8A29E]'
            }`}>{notes.length}</span>
          </button>

          {folders.map((folder) => (
            <div key={folder.folder_id} className="group relative">
              <button
                onClick={() => onSelectFolder(folder.folder_id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl transition-all duration-200 font-body text-sm ${
                  selectedFolder === folder.folder_id
                    ? "bg-gradient-to-r from-[#E06A4F]/10 to-[#E06A4F]/5 text-[#1C1917] shadow-md shadow-[#E7E5E4]/30"
                    : "text-[#78716C] hover:bg-white/60"
                }`}
                data-testid={`folder-${folder.folder_id}`}
              >
                <div 
                  className="w-2.5 h-2.5 rounded-full shadow-sm" 
                  style={{ backgroundColor: folder.color, boxShadow: selectedFolder === folder.folder_id ? `0 0 8px ${folder.color}` : 'none' }}
                />
                <span className="truncate font-medium">{folder.name}</span>
                <span className={`ml-auto text-xs font-medium px-2 py-0.5 rounded-full ${
                  selectedFolder === folder.folder_id ? 'bg-[#E06A4F] text-white' : 'bg-[#E7E5E4] text-[#A8A29E]'
                }`}>
                  {notes.filter(n => n.folder_id === folder.folder_id).length}
                </span>
              </button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-2 top-1/2 -translate-y-1/2 h-7 w-7 opacity-0 group-hover:opacity-100 transition-all duration-200 hover:bg-white/80"
                    data-testid={`folder-menu-${folder.folder_id}`}
                  >
                    <MoreHorizontal className="h-3.5 w-3.5 text-[#78716C]" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="backdrop-blur-xl">
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
        <div className="p-5 pb-3 flex items-center justify-between">
          <h3 className="text-xs font-semibold text-[#78716C] uppercase tracking-wider font-body">
            Notes
          </h3>
          <Button
            onClick={onCreateNote}
            variant="ghost"
            size="icon"
            className="h-7 w-7 hover:bg-white/60 hover:scale-110 transition-all duration-200"
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
                  className={`w-full text-left p-4 rounded-xl transition-all duration-300 group ${
                    selectedNote?.note_id === note.note_id
                      ? "bg-white shadow-lg shadow-[#E7E5E4]/40 border border-[#E7E5E4]/60 scale-[1.02]"
                      : "hover:bg-white/60 hover:shadow-md hover:shadow-[#E7E5E4]/20"
                  }`}
                  data-testid={`note-${note.note_id}`}
                >
                  <h4 className="font-heading font-medium text-[#1C1917] text-sm truncate mb-1.5 group-hover:text-[#E06A4F] transition-colors">
                    {note.title || "Untitled"}
                  </h4>
                  <p className="text-xs text-[#A8A29E] font-body truncate mb-2 leading-relaxed">
                    {getPreviewText(note.content) || "No content"}
                  </p>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-[#A8A29E] font-body bg-[#E7E5E4]/50 px-2 py-0.5 rounded-full">
                      {formatDate(note.updated_at)}
                    </span>
                  </div>
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