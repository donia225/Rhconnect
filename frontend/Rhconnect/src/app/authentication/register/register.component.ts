import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from 'src/app/services/auth/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [RouterModule,FormsModule,CommonModule],
  templateUrl: './register.component.html',
  styleUrl: './register.component.scss'
})
export class RegisterComponent {

  user: { 
    nom: string;
    prenom: string;
    email: string;
    password: string;
  } = {
    nom: '',
    prenom: '',
    email: '',
    password: ''
  };

  constructor(private authService: AuthService, private router: Router) {}

  register() {
    // Validation regex
    const nameRegex = /^[A-Za-zÀ-ÖØ-öø-ÿ\s'-]+$/;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
    
    // Check if any field is empty
  if (!this.user.nom || !this.user.prenom || !this.user.email || !this.user.password) {
    alert("Tous les champs sont obligatoires !");
    return;
  }
    // Name validation
    if (!nameRegex.test(this.user.nom)) {
      alert("Le nom ne doit contenir que des lettres.");
      return;
    }
    if (!nameRegex.test(this.user.prenom)) {
      alert("Le prénom ne doit contenir que des lettres.");
      return;
    }

    // Email validation
    if (!emailRegex.test(this.user.email)) {
      alert("Veuillez entrer une adresse email valide.");
      return;
    }

    // Password validation
    if (!passwordRegex.test(this.user.password)) {
      alert("Le mot de passe doit contenir au moins 8 caractères, incluant une lettre, un chiffre et un caractère spécial.");
      return;
    }

    // Call register API if all validations pass
    this.authService.register(this.user).subscribe({
      next: (response) => {
        console.log("Token received:", response.token);
        localStorage.setItem("access_token", response.token);
        this.router.navigate(["/auth/login"]); // Redirect to login
      },
      error: (error) => {
        console.error("Erreur lors de l’inscription", error);
        alert(error.error.message || "Erreur lors de l’inscription");
      }
    });
  }
}