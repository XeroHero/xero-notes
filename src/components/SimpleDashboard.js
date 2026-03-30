import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const SimpleDashboard = () => {
  const [notes, setNotes] = useState([]);
  const [newNote, setNewNote] = useState({ title: '', content: '' });
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user is logged in
    const user = localStorage.getItem('user');
    if (!user) {
      navigate('/simple-auth-debug');
    }
  }, [navigate]);

  const handleAddNote = () => {
    if (newNote.title.trim() && newNote.content.trim()) {
      const note = {
        id: Date.now().toString(),
        title: newNote.title,
        content: newNote.content,
        created_at: new Date().toISOString()
      };
      setNotes([...notes, note]);
      setNewNote({ title: '', content: '' });
    }
  };

  const handleDeleteNote = (id) => {
    setNotes(notes.filter(note => note.id !== id));
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Simple Dashboard</h1>
        <button
          onClick={() => navigate('/simple-auth-debug')}
          style={{
            padding: '8px 16px',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Logout
        </button>
      </div>
      
      <div style={{ marginBottom: '20px' }}>
        <h2>Create a Note</h2>
        <div style={{ marginBottom: '10px' }}>
          <input
            type="text"
            placeholder="Note title"
            value={newNote.title}
            onChange={(e) => setNewNote({ ...newNote, title: e.target.value })}
            style={{
              width: '100%',
              padding: '8px',
              marginBottom: '10px',
              border: '1px solid #ddd',
              borderRadius: '4px'
            }}
          />
        </div>
        <div style={{ marginBottom: '10px' }}>
          <textarea
            placeholder="Note content"
            value={newNote.content}
            onChange={(e) => setNewNote({ ...newNote, content: e.target.value })}
            rows={4}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              resize: 'vertical'
            }}
          />
        </div>
        <button
          onClick={handleAddNote}
          disabled={!newNote.title.trim() || !newNote.content.trim()}
          style={{
            width: '100%',
            padding: '10px',
            backgroundColor: (newNote.title.trim() && newNote.content.trim()) ? '#007bff' : '#ccc',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: (newNote.title.trim() && newNote.content.trim()) ? 'pointer' : 'not-allowed'
          }}
        >
          Add Note
        </button>
      </div>

      <div>
        <h2>Your Notes ({notes.length})</h2>
        {notes.length === 0 ? (
          <p style={{ textAlign: 'center', color: '#666' }}>No notes yet. Create your first note above!</p>
        ) : (
          <div style={{ display: 'grid', gap: '10px' }}>
            {notes.map(note => (
              <div
                key={note.id}
                style={{
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  padding: '15px',
                  backgroundColor: '#f9f9f9'
                }}
              >
                <h3 style={{ margin: '0 0 10px 0' }}>{note.title}</h3>
                <p style={{ margin: '0', color: '#666' }}>{note.content}</p>
                <div style={{ marginTop: '10px', textAlign: 'right' }}>
                  <small style={{ color: '#999' }}>
                    {new Date(note.created_at).toLocaleString()}
                  </small>
                  <button
                    onClick={() => handleDeleteNote(note.id)}
                    style={{
                      padding: '4px 8px',
                      backgroundColor: '#dc3545',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SimpleDashboard;
