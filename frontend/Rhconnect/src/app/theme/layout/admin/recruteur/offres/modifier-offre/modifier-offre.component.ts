import { Component, OnInit, OnDestroy, Renderer2, Inject } from '@angular/core';
import { CommonModule, DOCUMENT } from '@angular/common';
import { FormsModule, NgForm} from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { OffreService } from 'src/app/services/offre/offre.service';
import { SharedModule } from 'src/app/theme/shared/shared.module';

@Component({
  selector: 'app-modifier-offre',
  imports: [FormsModule,SharedModule, CommonModule],
  templateUrl: './modifier-offre.component.html',
  styleUrls: ['./modifier-offre.component.scss']
})
export class ModifierOffreComponent implements OnInit {
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
  { value: 'aucune', label: 'Aucune' },
  { value: 'moins_1_an', label: 'Moins de 1 an' },
  { value: 'entre_1_2_ans', label: '1 à 2 ans' },
  { value: 'entre_2_5_ans', label: '2 à 5 ans' },
  { value: 'entre_5_10_ans', label: '5 à 10 ans' },
  { value: 'plus_10_ans', label: 'Plus de 10 ans' },
];
DISPONIBILITES = [
  { value: 'plein_temps', label: 'Plein temps' },
  { value: 'mi_temps', label: 'Mi-temps' },
  { value: 'temps_partiel_weekend', label: 'Temps partiel (week-end)' },
  { value: 'temps_partiel_soir', label: 'Temps partiel (soir)' },
  { value: 'horaires_flexibles', label: 'Horaires flexibles' },
  { value: 'travail_en_shifts', label: 'Travail en shifts (2x8/3x8)' },
  { value: 'saisonnier', label: 'Saisonnier' },
];
MODALITES = [
  { value: 'sur_site', label: 'Sur site' },
  { value: 'hybride', label: 'Hybride' },
  { value: 'teletravail', label: 'Télétravail' },
];

  offreId!: number;
  offre = {
    titre: '',
    type_poste: '',
    experience: '',
    niveau_etude: '',
    disponibilite: '',
    modalite: '',
    langues: '',
    description: '',
    salaire: null as number | null,
    competences:''
  };
  niveauEtudeSel: string[] = [];
  titrePattern = "^(?=.*[A-Za-zÀ-ÖØ-öø-ÿ])[A-Za-zÀ-ÖØ-öø-ÿ' -]+$";

  languesPattern = "^([A-Za-zÀ-ÖØ-öø-ÿ' -]+)(\\s*,\\s*[A-Za-zÀ-ÖØ-öø-ÿ' -]+){0,2}$";
  languesError = "";
  SALAIRE_MIN = 300;
  SALAIRE_MAX = 20000;
  constructor(
    private route: ActivatedRoute,
    private offreService: OffreService,
    private router: Router, private toastr: ToastrService,
    private r: Renderer2,
    @Inject(DOCUMENT) private doc: Document
  ) {}

  ngOnInit(): void {
    this.r.addClass(this.doc.body, 'compact-offre');
    this.offreId = Number(this.route.snapshot.paramMap.get('id'));

    this.offreService.getAllOffres().subscribe((res: any[]) => {
      const current = res.find((o: any) => o.id === this.offreId);
      if (current) {
        this.offre = { ...current };
        const ne = current.niveau_etude;
        if (Array.isArray(ne)) {
          this.niveauEtudeSel = [...ne];
        } else if (typeof ne === 'string' && ne.trim()) {
          try {
            const parsed = JSON.parse(ne);
            this.niveauEtudeSel = Array.isArray(parsed)
              ? parsed.filter((x: any) => typeof x === 'string')
              : ne.split(/[,;]+/).map((s: string) => s.trim()).filter(Boolean);
          } catch {
            this.niveauEtudeSel = ne.split(/[,;]+/).map((s: string) => s.trim()).filter(Boolean);
          }
        }
      }
    });
  }
 onToggleNiveau(value: string, checked: boolean) {
  if (checked && !this.niveauEtudeSel.includes(value)) {
    this.niveauEtudeSel = [...this.niveauEtudeSel, value];
  } else if (!checked) {
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
  ngOnDestroy() {
  this.r.removeClass(this.doc.body, 'compact-offre');
}

  onSubmit(form: NgForm): void{
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

    this.offreService.modifierOffre(this.offreId, data).subscribe({
      next: () => {
        this.toastr.success("Offre modifiée avec succès !");
        this.router.navigate(['/admin/offres/liste']);
      },
      error: () => {
        alert('Erreur lors de la modification');
      }
    });
  }
    annuler() {
  this.router.navigate(['/admin/offres/liste']); // redirection vers la liste des offres
}
}
