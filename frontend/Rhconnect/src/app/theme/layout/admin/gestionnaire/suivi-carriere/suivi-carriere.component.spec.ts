import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';

import { SuiviCarriereComponent } from './suivi-carriere.component';

describe('SuiviCarriereComponent', () => {
  let component: SuiviCarriereComponent;
  let fixture: ComponentFixture<SuiviCarriereComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SuiviCarriereComponent],
      providers: [
  provideHttpClient(),
  provideHttpClientTesting(),
  {
    provide: ActivatedRoute,
    useValue: {
      snapshot: { paramMap: { get: () => null } },
      params: of({}),
      queryParams: of({})
    }
  }
]
    }).compileComponents();

    fixture = TestBed.createComponent(SuiviCarriereComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});