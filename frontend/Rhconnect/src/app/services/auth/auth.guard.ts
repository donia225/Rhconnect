import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {

  constructor(private router: Router) {}

  canActivate(): boolean {
    const token = localStorage.getItem('access_token');

    if (token) {
      return true;
    }

    // 🚫 Si pas de token → redirection vers login
    this.router.navigate(['/auth/login']);
    return false;
  }
}
