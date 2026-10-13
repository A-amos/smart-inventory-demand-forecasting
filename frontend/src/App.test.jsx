import { afterEach, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import App from './App';

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

test('signs in and revokes the server session when signing out', async () => {
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async url => {
    if (url.endsWith('/auth/login')) return { ok: true, status: 200, json: async () => ({ access_token: 'session-token', user: { name: 'Manager', role: 'manager' } }) };
    if (url.endsWith('/auth/logout')) return { ok: true, status: 204 };
    return { ok: true, status: 200, json: async () => [] };
  });
  render(<App/>);
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'manager@example.com' } });
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'test-password-123' } });
  fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));
  expect(await screen.findByText('Welcome, Manager')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Sign out' }));
  await waitFor(() => expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument());
  expect(fetchMock.mock.calls.find(([url]) => url.endsWith('/auth/logout'))[1].headers.Authorization).toBe('Bearer session-token');
});

test('shows failed sign-in and keeps protected content hidden', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue({ ok: false, status: 401, json: async () => ({ detail: 'Invalid credentials or account unavailable' }) });
  render(<App/>);
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'manager@example.com' } });
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong' } });
  fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Invalid credentials');
  expect(screen.queryByRole('button', { name: 'Sign out' })).not.toBeInTheDocument();
});
