import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { MonProfilComponent } from './mon-profil.component';

describe('MonProfilComponent', () => {
  let component: MonProfilComponent;
  let fixture: ComponentFixture<MonProfilComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MonProfilComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(MonProfilComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});