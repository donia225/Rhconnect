import { Component } from '@angular/core';
import { OffreService } from 'src/app/services/offre/offre.service';
import { FormsModule } from '@angular/forms';


@Component({
  selector: 'app-ajout-offre',
  imports: [FormsModule],
  templateUrl: './ajout-offre.component.html',
  styleUrl: './ajout-offre.component.scss'
})
export class AjoutOffreComponent {

  offre = {
    titre: '',
    description: '',
    salaire: null,
    competences:''
  };

  constructor(private offreService: OffreService) {}

  onSubmit() {
    const user = JSON.parse(localStorage.getItem('user_info') || '{}');
    const data = {
      ...this.offre,
      recruteur: user.id
    };
  
    console.log('Data envoyée au backend :', data); // 🐞 très utile
  
    this.offreService.ajouterOffre(data).subscribe({
      next: () => {
        alert("Offre ajoutée avec succès !");
      },
      error: (err) => {
        alert("Erreur lors de l’ajout");
        console.error(err);
      }
    });
  }
  
}