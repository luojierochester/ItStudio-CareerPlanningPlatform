import { jwtDecode } from 'jwt-decode';

interface JwtPayload {
  id: number;
  name: string;
  authorities: Array<{ authority: string }>;
  exp: number;
}

export function getAccountIdFromToken(): number | null {
  try {
    const token = localStorage.getItem('token');
    if (!token) return null;

    const decoded = jwtDecode<JwtPayload>(token);
    return decoded.id;
  } catch (error) {
    console.error('Failed to decode JWT:', error);
    return null;
  }
}
