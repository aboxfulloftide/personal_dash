import { useState, useEffect, useCallback } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import api from '../services/api';

// ─── Helpers ────────────────────────────────────────────────────────────────

const ACCESS_LEVELS = ['none', 'viewer', 'user', 'admin'];
const LEVEL_COLORS = {
  none:   'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400',
  viewer: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  user:   'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  admin:  'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
};

function LevelBadge({ level }) {
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${LEVEL_COLORS[level] || LEVEL_COLORS.none}`}>
      {level}
    </span>
  );
}

function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="px-6 py-4">{children}</div>
      </div>
    </div>
  );
}

function InputField({ label, type = 'text', value, onChange, placeholder, required, hint }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required={required}
        className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      {hint && <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{hint}</p>}
    </div>
  );
}

// ─── Users Tab ───────────────────────────────────────────────────────────────

function CreateUserModal({ apps, onClose, onCreated }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const res = await api.post('/admin/users', {
        email,
        password,
        display_name: displayName || undefined,
        is_admin: isAdmin,
      });
      onCreated(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create user');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title="Create User" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <InputField label="Email" type="email" value={email} onChange={setEmail} required />
        <InputField label="Password" type="password" value={password} onChange={setPassword} required />
        <InputField label="Display Name" value={displayName} onChange={setDisplayName} placeholder="Optional" />
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={isAdmin}
            onChange={(e) => setIsAdmin(e.target.checked)}
            className="w-4 h-4 text-blue-600 rounded border-gray-300"
          />
          <span className="text-sm text-gray-700 dark:text-gray-300">Site administrator (full access to all apps)</span>
        </label>
        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600">Cancel</button>
          <button type="submit" disabled={saving} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50">
            {saving ? 'Creating...' : 'Create User'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function EditUserModal({ user, apps, onClose, onUpdated }) {
  const [displayName, setDisplayName] = useState(user.display_name || '');
  const [isAdmin, setIsAdmin] = useState(user.is_admin);
  const [isActive, setIsActive] = useState(user.is_active);
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const { user: currentUser } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const payload = { display_name: displayName, is_admin: isAdmin, is_active: isActive };
      if (password) payload.password = password;
      const res = await api.patch(`/admin/users/${user.id}`, payload);
      onUpdated(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update user');
    } finally {
      setSaving(false);
    }
  };

  const isSelf = currentUser?.id === user.id;

  return (
    <Modal title={`Edit: ${user.email}`} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <InputField label="Display Name" value={displayName} onChange={setDisplayName} />
        <InputField label="New Password" type="password" value={password} onChange={setPassword} placeholder="Leave blank to keep current" />
        <div className="space-y-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              disabled={isSelf}
              className="w-4 h-4 text-blue-600 rounded border-gray-300"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">Active account</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={isAdmin}
              onChange={(e) => setIsAdmin(e.target.checked)}
              disabled={isSelf}
              className="w-4 h-4 text-blue-600 rounded border-gray-300"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">Site administrator</span>
          </label>
          {isSelf && <p className="text-xs text-gray-400">Cannot change your own active/admin status.</p>}
        </div>
        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600">Cancel</button>
          <button type="submit" disabled={saving} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50">
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function AccessModal({ user, apps, onClose, onChanged }) {
  const [access, setAccess] = useState(() => {
    const map = {};
    for (const a of user.app_access || []) map[a.app_id] = a.level;
    return map;
  });
  const [saving, setSaving] = useState(null);

  const handleChange = async (appId, level) => {
    setSaving(appId);
    try {
      if (level === '') {
        await api.delete(`/admin/users/${user.id}/access/${appId}`);
        setAccess((prev) => { const n = { ...prev }; delete n[appId]; return n; });
      } else {
        await api.put(`/admin/users/${user.id}/access/${appId}`, { level });
        setAccess((prev) => ({ ...prev, [appId]: level }));
      }
      onChanged();
    } catch {
      // ignore
    } finally {
      setSaving(null);
    }
  };

  return (
    <Modal title={`Access: ${user.display_name || user.email}`} onClose={onClose}>
      {user.is_admin ? (
        <p className="text-sm text-purple-600 dark:text-purple-400 mb-2">
          This user is a site administrator and has full access to all apps.
        </p>
      ) : (
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Set each app's access level. "No access" removes the entry entirely.
        </p>
      )}
      <div className="space-y-3">
        {apps.filter(a => a.is_active).map((app) => {
          const currentLevel = user.is_admin ? 'admin' : (access[app.id] || '');
          return (
            <div key={app.id} className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">{app.display_name}</p>
                <p className="text-xs text-gray-400 font-mono">{app.slug}</p>
              </div>
              {user.is_admin ? (
                <LevelBadge level="admin" />
              ) : (
                <select
                  value={currentLevel}
                  onChange={(e) => handleChange(app.id, e.target.value)}
                  disabled={saving === app.id}
                  className="text-sm border border-gray-300 dark:border-gray-600 rounded-md px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">No access</option>
                  {ACCESS_LEVELS.filter(l => l !== 'none').map(l => (
                    <option key={l} value={l}>{l.charAt(0).toUpperCase() + l.slice(1)}</option>
                  ))}
                </select>
              )}
            </div>
          );
        })}
      </div>
      <div className="flex justify-end mt-6">
        <button onClick={onClose} className="px-4 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600">
          Done
        </button>
      </div>
    </Modal>
  );
}

function UsersTab({ apps }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [editUser, setEditUser] = useState(null);
  const [accessUser, setAccessUser] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const { user: currentUser } = useAuth();

  const fetchUsers = useCallback(async () => {
    try {
      const res = await api.get('/admin/users');
      setUsers(res.data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  const handleDelete = async (u) => {
    if (!confirm(`Delete user ${u.email}? This cannot be undone.`)) return;
    setDeleting(u.id);
    try {
      await api.delete(`/admin/users/${u.id}`);
      setUsers((prev) => prev.filter((x) => x.id !== u.id));
    } catch {
      alert('Failed to delete user');
    } finally {
      setDeleting(null);
    }
  };

  if (loading) return <div className="text-center py-8 text-gray-400">Loading...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-gray-500 dark:text-gray-400">{users.length} user{users.length !== 1 ? 's' : ''}</p>
        <button
          onClick={() => setShowCreate(true)}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-1"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New User
        </button>
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-700/50 text-xs uppercase text-gray-500 dark:text-gray-400">
            <tr>
              <th className="px-4 py-3 text-left">User</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-left">App Access</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {users.map((u) => (
              <tr key={u.id} className="bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750">
                <td className="px-4 py-3">
                  <p className="font-medium text-gray-900 dark:text-white">
                    {u.display_name || u.email}
                    {u.id === currentUser?.id && (
                      <span className="ml-2 text-xs text-gray-400">(you)</span>
                    )}
                  </p>
                  {u.display_name && <p className="text-xs text-gray-400">{u.email}</p>}
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-col gap-1">
                    <span className={`inline-flex w-fit px-2 py-0.5 rounded text-xs font-medium ${u.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' : 'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400'}`}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </span>
                    {u.is_admin && <span className="inline-flex w-fit px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300">Admin</span>}
                  </div>
                </td>
                <td className="px-4 py-3">
                  {u.is_admin ? (
                    <span className="text-xs text-purple-600 dark:text-purple-400">All apps (admin)</span>
                  ) : (
                    <div className="flex flex-wrap gap-1">
                      {u.app_access.length === 0 ? (
                        <span className="text-xs text-gray-400">No access</span>
                      ) : (
                        u.app_access.map((a) => (
                          <span key={a.app_id} className="text-xs text-gray-600 dark:text-gray-300">
                            {a.app_name}: <LevelBadge level={a.level} />
                          </span>
                        ))
                      )}
                    </div>
                  )}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => setAccessUser(u)}
                      className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
                    >
                      Access
                    </button>
                    <button
                      onClick={() => setEditUser(u)}
                      className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-900/60"
                    >
                      Edit
                    </button>
                    {u.id !== currentUser?.id && (
                      <button
                        onClick={() => handleDelete(u)}
                        disabled={deleting === u.id}
                        className="px-2 py-1 text-xs bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400 rounded hover:bg-red-200 dark:hover:bg-red-900/60 disabled:opacity-50"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showCreate && (
        <CreateUserModal
          apps={apps}
          onClose={() => setShowCreate(false)}
          onCreated={(u) => { setUsers((prev) => [...prev, u]); setShowCreate(false); }}
        />
      )}
      {editUser && (
        <EditUserModal
          user={editUser}
          apps={apps}
          onClose={() => setEditUser(null)}
          onUpdated={(u) => {
            setUsers((prev) => prev.map((x) => (x.id === u.id ? u : x)));
            setEditUser(null);
          }}
        />
      )}
      {accessUser && (
        <AccessModal
          user={accessUser}
          apps={apps}
          onClose={() => setAccessUser(null)}
          onChanged={fetchUsers}
        />
      )}
    </div>
  );
}

// ─── Apps Tab ────────────────────────────────────────────────────────────────

function CreateAppModal({ onClose, onCreated }) {
  const [slug, setSlug] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      const res = await api.post('/admin/apps', { slug, display_name: displayName, description: description || undefined });
      onCreated(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create app');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title="Register App" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <InputField
          label="Slug"
          value={slug}
          onChange={setSlug}
          placeholder="my_app"
          required
          hint="Lowercase letters, digits, underscores. Used in JWT claims."
        />
        <InputField label="Display Name" value={displayName} onChange={setDisplayName} required />
        <InputField label="Description" value={description} onChange={setDescription} placeholder="Optional" />
        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600">Cancel</button>
          <button type="submit" disabled={saving} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50">
            {saving ? 'Registering...' : 'Register App'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function AppsTab({ apps, setApps }) {
  const [showCreate, setShowCreate] = useState(false);
  const [toggling, setToggling] = useState(null);
  const [deleting, setDeleting] = useState(null);

  const handleToggle = async (app) => {
    setToggling(app.id);
    try {
      const res = await api.patch(`/admin/apps/${app.id}`, { is_active: !app.is_active });
      setApps((prev) => prev.map((a) => (a.id === app.id ? res.data : a)));
    } catch {
      // ignore
    } finally {
      setToggling(null);
    }
  };

  const handleDelete = async (app) => {
    if (!confirm(`Delete app "${app.display_name}"? All user access entries will be removed.`)) return;
    setDeleting(app.id);
    try {
      await api.delete(`/admin/apps/${app.id}`);
      setApps((prev) => prev.filter((a) => a.id !== app.id));
    } catch {
      alert('Failed to delete app');
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-gray-500 dark:text-gray-400">{apps.length} registered app{apps.length !== 1 ? 's' : ''}</p>
        <button
          onClick={() => setShowCreate(true)}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-1"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Register App
        </button>
      </div>

      <div className="space-y-3">
        {apps.map((app) => (
          <div
            key={app.id}
            className={`flex items-start justify-between p-4 rounded-lg border ${app.is_active ? 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800' : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 opacity-60'}`}
          >
            <div>
              <div className="flex items-center gap-2">
                <p className="font-medium text-gray-900 dark:text-white">{app.display_name}</p>
                <span className="font-mono text-xs text-gray-400 bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">{app.slug}</span>
                {!app.is_active && <span className="text-xs text-gray-400">inactive</span>}
              </div>
              {app.description && <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{app.description}</p>}
            </div>
            <div className="flex items-center gap-2 ml-4 flex-shrink-0">
              <button
                onClick={() => handleToggle(app)}
                disabled={toggling === app.id}
                className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50"
              >
                {app.is_active ? 'Deactivate' : 'Activate'}
              </button>
              <button
                onClick={() => handleDelete(app)}
                disabled={deleting === app.id}
                className="px-2 py-1 text-xs bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400 rounded hover:bg-red-200 dark:hover:bg-red-900/60 disabled:opacity-50"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
        <h3 className="text-sm font-semibold text-blue-800 dark:text-blue-300 mb-2">Integrating a New App</h3>
        <p className="text-xs text-blue-700 dark:text-blue-400 mb-2">
          After registering an app, other services on this server can validate Personal Dash JWTs using the shared secret:
        </p>
        <pre className="text-xs bg-blue-100 dark:bg-blue-900/40 text-blue-900 dark:text-blue-200 rounded p-3 overflow-x-auto whitespace-pre-wrap">{`# In your app's .env:
PERSONAL_DASH_SECRET_KEY=<same SECRET_KEY as personal_dash>

# Python validation snippet (auth_client.py):
from jose import jwt, JWTError
import os

SECRET = os.getenv("PERSONAL_DASH_SECRET_KEY")
LEVELS = {"none": 0, "viewer": 1, "user": 2, "admin": 3}

def require_access(token: str, app_slug: str, min_level="viewer"):
    payload = jwt.decode(token, SECRET, algorithms=["HS256"],
                         options={"leeway": 30})
    if payload.get("type") != "access":
        raise ValueError("Not an access token")
    apps = payload.get("apps", {})
    level = apps.get(app_slug, "none")
    if LEVELS.get(level, 0) < LEVELS[min_level]:
        raise ValueError(f"Need {min_level}, have {level}")
    return payload`}
        </pre>
        <p className="text-xs text-blue-700 dark:text-blue-400 mt-2">
          Or call <code className="bg-blue-100 dark:bg-blue-900/40 px-1 rounded">POST /api/v1/auth/verify</code> with the bearer token for non-Python services.
        </p>
      </div>

      {showCreate && (
        <CreateAppModal
          onClose={() => setShowCreate(false)}
          onCreated={(a) => { setApps((prev) => [...prev, a]); setShowCreate(false); }}
        />
      )}
    </div>
  );
}

// ─── Settings Tab ────────────────────────────────────────────────────────────

function SettingsTab() {
  const [intervalHours, setIntervalHours] = useState('');
  const [retentionDays, setRetentionDays] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/admin/settings/speedtest')
      .then((r) => {
        setIntervalHours(String(r.data.interval_hours));
        setRetentionDays(String(r.data.retention_days));
      })
      .catch(() => setError('Failed to load settings'))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSaved(false);
    try {
      await api.put('/admin/settings/speedtest', {
        interval_hours: parseFloat(intervalHours),
        retention_days: parseInt(retentionDays, 10),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="text-sm text-gray-500 dark:text-gray-400">Loading…</p>;

  return (
    <div className="space-y-6 max-w-lg">
      <div>
        <h2 className="text-base font-semibold text-gray-900 dark:text-white mb-1">Speed Test Schedule</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          The server runs a speed test automatically and stores results for all users.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-4">
        <InputField
          label="Interval (hours)"
          type="number"
          value={intervalHours}
          onChange={setIntervalHours}
          hint="How often to auto-run a speed test. Min 0.25 (15 min), e.g. 6 = every 6 hours."
        />
        <InputField
          label="Retention (days)"
          type="number"
          value={retentionDays}
          onChange={setRetentionDays}
          hint="How many days of speed test history to keep."
        />

        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}

        <button
          type="submit"
          disabled={saving}
          className="px-4 py-2 text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-md disabled:opacity-50"
        >
          {saving ? 'Saving…' : saved ? 'Saved!' : 'Save'}
        </button>
      </form>
    </div>
  );
}

// ─── Page shell ──────────────────────────────────────────────────────────────

const TABS = ['Users', 'Apps', 'Settings'];

export default function AdminPage() {
  const { user } = useAuth();
  const { darkMode, toggleDarkMode } = useTheme();
  const [activeTab, setActiveTab] = useState('Users');
  const [apps, setApps] = useState([]);

  useEffect(() => {
    api.get('/admin/apps').then((r) => setApps(r.data)).catch(() => {});
  }, []);

  if (!user) return null;
  if (!user.is_admin) return <Navigate to="/" replace />;

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/" className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Link>
            <h1 className="text-lg font-bold text-gray-900 dark:text-white">Admin</h1>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500 dark:text-gray-400 hidden sm:inline">{user.display_name || user.email}</span>
            <button
              onClick={toggleDarkMode}
              className="p-2 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md"
            >
              {darkMode ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-6">
        {/* Tabs */}
        <div className="border-b border-gray-200 dark:border-gray-700 mb-6">
          <nav className="flex gap-1">
            {TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 text-sm font-medium rounded-t-md border-b-2 transition-colors ${
                  activeTab === tab
                    ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>

        {activeTab === 'Users' && <UsersTab apps={apps} />}
        {activeTab === 'Apps' && <AppsTab apps={apps} setApps={setApps} />}
        {activeTab === 'Settings' && <SettingsTab />}
      </main>
    </div>
  );
}
