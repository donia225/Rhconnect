import { Component, OnInit, OnDestroy, Renderer2, Inject } from '@angular/core';
import { OffreService } from 'src/app/services/offre/offre.service';
import { FormsModule, NgForm  } from '@angular/forms';
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
    modalite:'',
    langues: '',
    description: '',
    salaire: null as number | null,
    competences:''
  };
 NIVEAUX_ETUDE = [
    { value: 'bac',       label: 'Baccalauréat' },
    { value: 'bac+2',     label: 'Bac+2 (BTS/DUT/ISET)' },
    { value: 'licence',   label: 'Licence (Bac+3)' },
    { value: 'master',    label: 'Master / Mastère (Bac+5)' },
    { value: 'ingenieur', label: "Diplôme d'ingénieur (Bac+5)" },
    { value: 'mba',       label: 'MBA / Mastère spécialisé' },
    { value: 'doctorat',  label: 'Doctorat' }
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
DISPONIBILITES = [
  { value: 'plein_temps',           label: 'Plein temps' },
  { value: 'mi_temps',              label: 'Mi-temps' },
  { value: 'temps_partiel_weekend', label: 'Temps partiel (week-end)' },
  { value: 'temps_partiel_soir',    label: 'Temps partiel (soir)' },
  { value: 'horaires_flexibles',    label: 'Horaires flexibles' },
  { value: 'travail_en_shifts',     label: 'Travail en shifts (2x8/3x8)' },
  { value: 'saisonnier',            label: 'Saisonnier' },
];
MODALITES = [
  { value: 'sur_site', label: 'Sur site' },
  { value: 'hybride',  label: 'Hybride' },
  { value: 'teletravail', label: 'Télétravail' },
];
submitted=false;
titrePattern = "^(?=.*[A-Za-zÀ-ÖØ-öø-ÿ])[A-Za-zÀ-ÖØ-öø-ÿ' -]+$";
competencesPattern =
  '^(?:(?=[A-Za-z0-9À-ÖØ-öø-ÿ+\\#\\.\\- ]*[A-Za-zÀ-ÖØ-öø-ÿ])[A-Za-z0-9À-ÖØ-öø-ÿ+\\#\\.\\- ]+)'+
  '(?:\\s*,\\s*(?=[A-Za-z0-9À-ÖØ-öø-ÿ+\\#\\.\\- ]*[A-Za-zÀ-ÖØ-öø-ÿ])[A-Za-z0-9À-ÖØ-öø-ÿ+\\#\\.\\- ]+)*$';
languesPattern = "^([A-Za-zÀ-ÖØ-öø-ÿ' -]+)(\\s*,\\s*[A-Za-zÀ-ÖØ-öø-ÿ' -]+){0,2}$";
languesError = "";
SALAIRE_MIN = 300;
SALAIRE_MAX = 20000;


niveauEtudeSel: string[] = [];
  constructor(private offreService: OffreService, private toastr: ToastrService, private router: Router, private r: Renderer2, @Inject(DOCUMENT) private doc: Document) {}

   ngOnInit() {
    this.r.addClass(this.doc.body, 'compact-offre');

  }
    ngOnDestroy() {
    this.r.removeClass(this.doc.body, 'compact-offre');
  }
  onToggleNiveau(value: string, checked: boolean) {
    if (checked) {
      if (!this.niveauEtudeSel.includes(value)) {
        this.niveauEtudeSel = [...this.niveauEtudeSel, value];
      }
    } else {
      this.niveauEtudeSel = this.niveauEtudeSel.filter(v => v !== value);
    }
  }
onLangChange(val: string) {
  this.offre.langues = val;
  const langs = (val || '')
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);
  this.languesError = langs.length > 3 ? 'Maximum 3 langues (séparées par une virgule).' : '';
}
  onSubmit(form: NgForm) {
  this.submitted = true;
  if (this.niveauEtudeSel.length === 0) return;
  if (this.languesError) return;

  if (form.invalid) return;
    const user = JSON.parse(localStorage.getItem('user_info') || '{}');
    const data = {
      ...this.offre,
      titre: (this.offre.titre || '').trim(),
      description: (this.offre.description || '').trim(),
      salaire: this.offre.salaire != null ? Number(this.offre.salaire) : null,
      niveau_etude: [...this.niveauEtudeSel], 
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