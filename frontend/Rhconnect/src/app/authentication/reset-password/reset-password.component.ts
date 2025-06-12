import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { AuthService } from 'src/app/services/auth/auth.service';


@Component({
  selector: 'app-reset-password',
  imports: [FormsModule, CommonModule],
  templateUrl: './reset-password.component.html',
  styleUrl: './reset-password.component.scss'
})
export class ResetPasswordComponent implements OnInit {
  email = '';
  password = '';
  confirmPassword = '';
  uid: string | null = null;
  token: string | null = null;
  message = '';
  error = '';

  constructor(private route: ActivatedRoute, private http: HttpClient, private router: Router, private authService:AuthService) {}

  ngOnInit(): void {
    this.uid = this.route.snapshot.paramMap.get('uid');
    this.token = this.route.snapshot.paramMap.get('token');
  }
  get passwordMismatch(): boolean {
  return this.password && this.confirmPassword && this.password !== this.confirmPassword;
}


 submit() {
  if (this.uid && this.token) {
    if (this.password !== this.confirmPassword) {
      this.error = 'Les mots de passe ne correspondent pas.';
      return;
    }
    this.authService.resetPassword(this.uid, this.token, this.password, this.confirmPassword)
      .subscribe({
        next: () => {
          this.message = 'Mot de passe mis à jour.';
          this.router.navigate(['/auth/login']);
        },
        error: (err) => {
          this.error = err.error?.error || 'Erreur.';
        }
      });
  } else {
    this.authService.requestPasswordReset(this.email).subscribe({
      next: () => this.message = 'Si cet email est valide, un lien a été envoyé.',
      error: () => this.error = 'Erreur lors de l’envoi.'
    });
  }
}
}