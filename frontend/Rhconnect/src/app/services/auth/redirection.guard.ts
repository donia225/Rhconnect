// redirection.guard.ts
import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from './auth.service';

@Injectable({ providedIn: 'root' })
export class RedirectionGuard implements CanActivate {
  constructor(private auth: AuthService, private router: Router) {}

canActivate(): boolean {
  const user = this.auth.getUserInfo();
  if (user) {
    if (user.role === 'gestionnaire_rh' || user.role === 'recruteur') {
      this.router.navigate(['/admin/dashboard']);
    } else if (user.role === 'employe') {
      this.router.navigate(['/employe/profil']);
    } else if (user.role === 'candidat') {
      return true; // ✅ laisser passer pour accéder à `/` (AccueilComponent)
    } else {
      this.router.navigate(['/unauthorized']); // facultatif
    }
    return false;
  }
  return true;
}

}
