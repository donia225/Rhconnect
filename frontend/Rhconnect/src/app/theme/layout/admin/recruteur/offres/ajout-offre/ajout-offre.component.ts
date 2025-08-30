import { Component, OnInit, OnDestroy, Renderer2, Inject } from '@angular/core';
import { OffreService } from 'src/app/services/offre/offre.service';
import { FormsModule } from '@angular/forms';
import { CommonModule, DOCUMENT } from '@angular/common';
import { SharedModule } from 'src/app/theme/shared/shared.module';
import { ToastrService } from 'ngx-toastr';
import { Router } from '@angular/router';


@Component({
  selector: 'app-ajout-offre',
  imports: [FormsModule, CommonModule, SharedModule],
  templateUrl: './ajout-offre.component.html',
  styleUrl: './ajout-offre.component.scss'
})
export class AjoutOffreComponent implements OnInit, OnDestroy{

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
 NIVEAUX_ETUDE = [
  { value: 'licence',     label: 'Licence' },
  { value: 'master',      label: 'Master' },
  { value: 'ingénierie',  label: 'Ingénierie' },
  { value: 'doctorat',    label: 'Doctorat' },
  { value: 'expert',      label: 'Expert' },
  { value: 'recherche',   label: 'Chercheur/Recherche' },
];

TYPES_POSTE = ['CDI', 'CDD', 'SIVP'];

EXPERIENCES = [
  { value: 'aucune',         label: 'Aucune' },
  { value: 'moins_1_an',     label: 'Moins de 1 an' },
  { value: 'entre_1_2_ans',  label: '1 à 2 ans' },
  { value: 'entre_2_5_ans',  label: '2 à 5 ans' },
  { value: 'entre_5_10_ans', label: '5 à 10 ans' },
  { value: 'plus_10_ans',    label: 'Plus de 10 ans' },
];

  constructor(private offreService: OffreService, private toastr: ToastrService, private router: Router, private r: Renderer2, @Inject(DOCUMENT) private doc: Document) {}

   ngOnInit() {
    this.r.addClass(this.doc.body, 'compact-offre');

  }
    ngOnDestroy() {
    this.r.removeClass(this.doc.body, 'compact-offre');
  }
  onSubmit() {
    const user = JSON.parse(localStorage.getItem('user_info') || '{}');
    const data = {
      ...this.offre,
      recruteur: user.id
    };
  
    console.log('Data envoyée au backend :', data);
  
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