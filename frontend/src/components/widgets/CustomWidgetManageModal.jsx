import { useEffect, useState } from 'react';
import api from '../../services/api';

const EMPTY_FORM = {
  title: '',
  subtitle: '',
  description: '',
  icon: '',
  link_url: '',
  link_text: '',
  visible: true,
  highlight: false,
  color: '',
  priority: 0,
  alert_active: false,
  alert_severity: '',
  alert_message: '',
};

function Label({ children }) {
  return (
    <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-0.5">
      {children}
    </label>
  );
}

function Input({ value, onChange, placeholder, type = 'text', ...rest }) {
  return (
    <input
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      className="w-full text-sm px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
      {...rest}
    />
  );
}

function Toggle({ label, checked, onChange }) {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <div
        className={`relative w-9 h-5 rounded-full transition-colors ${checked ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'}`}
        onClick={() => onChange(!checked)}
      >
        <div className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${checked ? 'translate-x-4' : 'translate-x-0'}`} />
      </div>
      <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
    </label>
  );
}

function ItemForm({ initial, widgetId, onSaved, onCancel }) {
  const [form, setForm] = useState({ ...EMPTY_FORM, ...initial });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  const setVal = (field) => (val) => setForm((f) => ({ ...f, [field]: val }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title.trim()) {
      setError('Title is required');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const payload = {
        ...form,
        priority: parseInt(form.priority, 10) || 0,
        alert_severity: form.alert_severity || null,
        color: form.color || null,
        subtitle: form.subtitle || null,
        description: form.description || null,
        icon: form.icon || null,
        link_url: form.link_url || null,
        link_text: form.link_text || null,
        alert_message: form.alert_message || null,
      };
      if (initial?.id) {
        await api.put(`/custom-widgets/${widgetId}/items/${initial.id}`, payload);
      } else {
        await api.post(`/custom-widgets/${widgetId}/items`, payload);
      }
      onSaved();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save item');
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
        {initial?.id ? 'Edit Item' : 'Add Item'}
      </h3>

      {error && (
        <div className="p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-xs text-red-600 dark:text-red-400">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <Label>Title *</Label>
          <Input value={form.title} onChange={set('title')} placeholder="Item title" />
        </div>
        <div className="col-span-2">
          <Label>Subtitle</Label>
          <Input value={form.subtitle} onChange={set('subtitle')} placeholder="Optional subtitle" />
        </div>
        <div className="col-span-2">
          <Label>Description</Label>
          <Input value={form.description} onChange={set('description')} placeholder="Optional description" />
        </div>
        <div>
          <Label>Icon (emoji)</Label>
          <Input value={form.icon} onChange={set('icon')} placeholder="✅" />
        </div>
        <div>
          <Label>Priority</Label>
          <Input type="number" value={form.priority} onChange={set('priority')} />
        </div>
        <div>
          <Label>Link URL</Label>
          <Input value={form.link_url} onChange={set('link_url')} placeholder="https://..." />
        </div>
        <div>
          <Label>Link Text</Label>
          <Input value={form.link_text} onChange={set('link_text')} placeholder="Open →" />
        </div>
        <div>
          <Label>Color</Label>
          <select
            value={form.color}
            onChange={set('color')}
            className="w-full text-sm px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">None</option>
            <option value="red">Red</option>
            <option value="yellow">Yellow</option>
            <option value="green">Green</option>
            <option value="blue">Blue</option>
          </select>
        </div>
        <div className="flex items-end pb-1">
          <Toggle label="Highlight" checked={form.highlight} onChange={setVal('highlight')} />
        </div>
        <div className="flex items-end pb-1">
          <Toggle label="Visible" checked={form.visible} onChange={setVal('visible')} />
        </div>
      </div>

      {/* Alert section */}
      <div className="border-t border-gray-200 dark:border-gray-700 pt-3 space-y-2">
        <Toggle label="Alert Active" checked={form.alert_active} onChange={setVal('alert_active')} />
        {form.alert_active && (
          <div className="grid grid-cols-2 gap-3 mt-2">
            <div>
              <Label>Alert Severity</Label>
              <select
                value={form.alert_severity}
                onChange={set('alert_severity')}
                className="w-full text-sm px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="">Info</option>
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <div>
              <Label>Alert Message</Label>
              <Input value={form.alert_message} onChange={set('alert_message')} placeholder="Alert description" />
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving}
          className="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded"
        >
          {saving ? 'Saving…' : 'Save'}
        </button>
      </div>
    </form>
  );
}

export default function CustomWidgetManageModal({ widgetId, onClose }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('list'); // 'list' | 'form'
  const [editItem, setEditItem] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);

  const fetchItems = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/custom-widgets/${widgetId}/items/all`);
      setItems(res.data);
    } catch (err) {
      console.error('Failed to load items:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, [widgetId]);

  const handleDelete = async (itemId) => {
    if (confirmDeleteId !== itemId) {
      setConfirmDeleteId(itemId);
      return;
    }
    try {
      await api.delete(`/custom-widgets/${widgetId}/items/${itemId}`);
      setConfirmDeleteId(null);
      fetchItems();
    } catch (err) {
      console.error('Failed to delete item:', err);
    }
  };

  const handleToggleVisible = async (item) => {
    try {
      await api.put(`/custom-widgets/${widgetId}/items/${item.id}`, {
        ...item,
        visible: !item.visible,
        alert_severity: item.alert_severity || null,
        color: item.color || null,
      });
      fetchItems();
    } catch (err) {
      console.error('Failed to toggle visibility:', err);
    }
  };

  const handleAcknowledgeItem = async (itemId) => {
    try {
      await api.post(`/custom-widgets/${widgetId}/items/${itemId}/acknowledge`);
      fetchItems();
    } catch (err) {
      console.error('Failed to acknowledge item:', err);
    }
  };

  const openAdd = () => {
    setEditItem(null);
    setView('form');
  };

  const openEdit = (item) => {
    setEditItem(item);
    setView('form');
  };

  const handleSaved = () => {
    setView('list');
    setEditItem(null);
    fetchItems();
  };

  const handleCancel = () => {
    setView('list');
    setEditItem(null);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-lg max-h-[90vh] flex flex-col shadow-xl">
        {/* Modal header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">
            Manage Items
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal body */}
        <div className="flex-1 overflow-y-auto p-4">
          {view === 'form' ? (
            <ItemForm
              initial={editItem}
              widgetId={widgetId}
              onSaved={handleSaved}
              onCancel={handleCancel}
            />
          ) : (
            <>
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {items.length} item{items.length !== 1 ? 's' : ''}
                </span>
                <button
                  onClick={openAdd}
                  className="flex items-center gap-1 text-sm bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded"
                >
                  <span>+</span> Add Item
                </button>
              </div>

              {loading ? (
                <div className="text-center py-8 text-gray-400 dark:text-gray-500 text-sm">Loading…</div>
              ) : items.length === 0 ? (
                <div className="text-center py-8 text-gray-400 dark:text-gray-500">
                  <div className="text-3xl mb-2">📋</div>
                  <div className="text-sm">No items yet. Add one above.</div>
                </div>
              ) : (
                <ul className="space-y-2">
                  {items.map((item) => (
                    <li
                      key={item.id}
                      className="flex items-center gap-2 p-2 rounded border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/40"
                    >
                      {item.icon && (
                        <span className="text-sm flex-shrink-0">{item.icon}</span>
                      )}
                      <div className="flex-1 min-w-0">
                        <div className={`text-sm font-medium truncate ${item.visible ? 'text-gray-800 dark:text-gray-200' : 'text-gray-400 dark:text-gray-500 line-through'}`}>
                          {item.title}
                        </div>
                        {item.subtitle && (
                          <div className="text-xs text-gray-500 dark:text-gray-400 truncate">{item.subtitle}</div>
                        )}
                      </div>
                      {item.alert_active && !item.acknowledged && (
                        <button
                          onClick={() => handleAcknowledgeItem(item.id)}
                          title="Acknowledge alert"
                          className="flex-shrink-0 text-xs px-1.5 py-0.5 rounded bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50"
                        >
                          alert
                        </button>
                      )}
                      {item.alert_active && item.acknowledged && (
                        <span className="flex-shrink-0 text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500">
                          ack'd
                        </span>
                      )}

                      {/* Visibility toggle */}
                      <button
                        onClick={() => handleToggleVisible(item)}
                        title={item.visible ? 'Hide item' : 'Show item'}
                        className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                      >
                        {item.visible ? (
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                        ) : (
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                          </svg>
                        )}
                      </button>

                      {/* Edit */}
                      <button
                        onClick={() => openEdit(item)}
                        title="Edit"
                        className="flex-shrink-0 p-1 text-gray-400 hover:text-blue-500"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                      </button>

                      {/* Delete (2-click confirm) */}
                      {confirmDeleteId === item.id ? (
                        <button
                          onClick={() => handleDelete(item.id)}
                          className="flex-shrink-0 text-xs px-2 py-0.5 bg-red-600 hover:bg-red-700 text-white rounded"
                        >
                          Confirm
                        </button>
                      ) : (
                        <button
                          onClick={() => handleDelete(item.id)}
                          title="Delete"
                          className="flex-shrink-0 p-1 text-gray-400 hover:text-red-500"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
