import { Component } from '@angular/core';
import { OffreService } from 'src/app/services/offre/offre.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { SharedModule } from 'src/app/theme/shared/shared.module';
import { ToastrService } from 'ngx-toastr';
import { Router } from '@angular/router';


@Component({
  selector: 'app-ajout-offre',
  imports: [FormsModule, CommonModule, SharedModule],
  templateUrl: './ajout-offre.component.html',
  styleUrl: './ajout-offre.component.scss'
})
export class AjoutOffreComponent {

  offre = {
    titre: '',
    type_poste: '',
    experience: '',
    niveau_etude: '',
    disponibilite: '',
    langues: '',
    description: '',
    salaire: null,
    competences:''
  };

  constructor(private offreService: OffreService, private toastr: ToastrService, private router: Router) {}

  onSubmit() {
    const user = JSON.parse(localStorage.getItem('user_info') || '{}');
    const data = {
      ...this.offre,
      recruteur: user.id
    };
  
    console.log('Data envoyée au backend :', data); // 🐞 très utile
  
    this.offreService.ajouterOffre(data).subscribe({
      next: () => {
      this.toastr.success('Offre ajoutée avec succès');
      this.router.navigate(['/admin/offres/liste']);
      },
      error: (err) => {
        alert("Erreur lors de l’ajout");
        console.error(err);
      }
    });
  }
  annuler() {
  this.router.navigate(['/admin/offres/liste']); // redirection vers la liste des offres
}

  
}