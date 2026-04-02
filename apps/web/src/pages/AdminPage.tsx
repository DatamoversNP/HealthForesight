/**
 * Admin – user management and role-based access
 */
import { useState, useEffect } from 'react'
import {
  Box,
  Container,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Checkbox,
  Chip,
  IconButton,
} from '@mui/material'
import { AdminPanelSettings as AdminIcon, PersonAdd as AddIcon, Edit as EditIcon } from '@mui/icons-material'
import { apiClient } from '../lib/api'

interface UserRow {
  id: string
  tenant_id: string
  email: string
  full_name: string | null
  is_active: string
  auth_source?: string
  role_names: string[]
  created_at: string | null
}

interface RoleOption {
  id: string
  name: string
  description: string | null
}

export default function AdminPage() {
  const [users, setUsers] = useState<UserRow[]>([])
  const [roles, setRoles] = useState<RoleOption[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<UserRow | null>(null)
  const [createEmail, setCreateEmail] = useState('')
  const [createFullName, setCreateFullName] = useState('')
  const [createPassword, setCreatePassword] = useState('')
  const [createRoleNames, setCreateRoleNames] = useState<string[]>([])
  const [editRoleNames, setEditRoleNames] = useState<string[]>([])
  const [editFullName, setEditFullName] = useState('')
  const [editActive, setEditActive] = useState(true)
  const [editPassword, setEditPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const loadUsers = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiClient.listUsers({ limit: 100 })
      setUsers(Array.isArray(data) ? data : [])
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to load users')
      setUsers([])
    } finally {
      setLoading(false)
    }
  }

  const loadRoles = async () => {
    try {
      const data = await apiClient.getAccessRoles()
      setRoles(Array.isArray(data) ? data : [])
    } catch {
      setRoles([])
    }
  }

  useEffect(() => {
    loadUsers()
    loadRoles()
  }, [])

  const handleCreate = async () => {
    if (!createEmail.trim()) return
    setSubmitting(true)
    try {
      await apiClient.createUser({
        email: createEmail.trim(),
        full_name: createFullName.trim() || undefined,
        role_names: createRoleNames,
        password: createPassword.trim() || undefined,
      })
      setCreateOpen(false)
      setCreateEmail('')
      setCreateFullName('')
      setCreatePassword('')
      setCreateRoleNames([])
      loadUsers()
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Create failed')
    } finally {
      setSubmitting(false)
    }
  }

  const openEdit = (user: UserRow) => {
    setSelectedUser(user)
    setEditRoleNames(user.role_names || [])
    setEditFullName(user.full_name || '')
    setEditActive(user.is_active !== 'false')
    setEditPassword('')
    setEditOpen(true)
  }

  const handleEdit = async () => {
    if (!selectedUser) return
    setSubmitting(true)
    try {
      const payload: { full_name?: string; is_active?: string; role_names?: string[]; password?: string } = {
        full_name: editFullName.trim() || undefined,
        is_active: editActive ? 'true' : 'false',
        role_names: editRoleNames,
      }
      if (selectedUser.auth_source === 'local' && editPassword.trim()) {
        payload.password = editPassword.trim()
      }
      await apiClient.updateAccessUser(selectedUser.id, payload)
      setEditOpen(false)
      setSelectedUser(null)
      loadUsers()
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Update failed')
    } finally {
      setSubmitting(false)
    }
  }

  const toggleCreateRole = (name: string) => {
    setCreateRoleNames((prev) =>
      prev.includes(name) ? prev.filter((r) => r !== name) : [...prev, name]
    )
  }

  const toggleEditRole = (name: string) => {
    setEditRoleNames((prev) =>
      prev.includes(name) ? prev.filter((r) => r !== name) : [...prev, name]
    )
  }

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <AdminIcon sx={{ fontSize: 36, color: 'primary.main' }} />
        <Typography variant="h5" fontWeight={600}>
          Admin – User Management &amp; Security
        </Typography>
      </Box>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Manage users and role-based access. Only POLICY_ADMIN can create or edit users.
      </Typography>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Users</Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateOpen(true)}
          >
            Add user
          </Button>
        </Box>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: 'action.hover' }}>
                  <TableCell sx={{ fontWeight: 600 }}>Email</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Name</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Sign-in</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Roles</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600 }}>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 3 }}>
                      No users yet. Add a user to get started.
                    </TableCell>
                  </TableRow>
                ) : (
                  users.map((u) => (
                    <TableRow key={u.id}>
                      <TableCell>{u.email}</TableCell>
                      <TableCell>{u.full_name || '—'}</TableCell>
                      <TableCell>
                        <Chip
                          label={u.auth_source === 'oidc' ? 'Azure AD / SSO' : 'Email & password'}
                          size="small"
                          variant="outlined"
                          color={u.auth_source === 'oidc' ? 'primary' : 'default'}
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {(u.role_names || []).map((r) => (
                            <Chip key={r} label={r} size="small" variant="outlined" />
                          ))}
                          {(!u.role_names || u.role_names.length === 0) && '—'}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={u.is_active === 'false' ? 'Inactive' : 'Active'}
                          size="small"
                          color={u.is_active === 'false' ? 'default' : 'success'}
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <IconButton size="small" onClick={() => openEdit(u)} title="Edit user">
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Create user dialog */}
      <Dialog open={createOpen} onClose={() => !submitting && setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add user</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Email"
            type="email"
            fullWidth
            value={createEmail}
            onChange={(e) => setCreateEmail(e.target.value)}
            required
          />
          <TextField
            margin="dense"
            label="Full name"
            fullWidth
            value={createFullName}
            onChange={(e) => setCreateFullName(e.target.value)}
          />
          <TextField
            margin="dense"
            label="Password (optional – for email/password sign-in)"
            type="password"
            fullWidth
            value={createPassword}
            onChange={(e) => setCreatePassword(e.target.value)}
            helperText="Leave blank to set later or for SSO-only users."
          />
          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Roles
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {roles.map((r) => (
              <FormControlLabel
                key={r.id}
                control={
                  <Checkbox
                    checked={createRoleNames.includes(r.name)}
                    onChange={() => toggleCreateRole(r.name)}
                  />
                }
                label={r.name}
              />
            ))}
            {roles.length === 0 && (
              <Typography color="text.secondary" variant="body2">
                No roles loaded. Ensure you have POLICY_ADMIN access.
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)} disabled={submitting}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate} disabled={submitting || !createEmail.trim()}>
            {submitting ? 'Creating…' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit user dialog */}
      <Dialog open={editOpen} onClose={() => !submitting && setEditOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit user {selectedUser?.email}</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            label="Full name"
            fullWidth
            value={editFullName}
            onChange={(e) => setEditFullName(e.target.value)}
          />
          <FormControlLabel
            control={
              <Checkbox checked={editActive} onChange={(e) => setEditActive(e.target.checked)} />
            }
            label="Active"
          />
          {selectedUser?.auth_source === 'local' && (
            <TextField
              margin="dense"
              label="New password (leave blank to keep current)"
              type="password"
              fullWidth
              value={editPassword}
              onChange={(e) => setEditPassword(e.target.value)}
            />
          )}
          {selectedUser?.auth_source === 'oidc' && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              SSO users sign in via Azure AD; password cannot be set here.
            </Typography>
          )}
          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            Roles
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {roles.map((r) => (
              <FormControlLabel
                key={r.id}
                control={
                  <Checkbox
                    checked={editRoleNames.includes(r.name)}
                    onChange={() => toggleEditRole(r.name)}
                  />
                }
                label={r.name}
              />
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditOpen(false)} disabled={submitting}>Cancel</Button>
          <Button variant="contained" onClick={handleEdit} disabled={submitting}>
            {submitting ? 'Saving…' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}
