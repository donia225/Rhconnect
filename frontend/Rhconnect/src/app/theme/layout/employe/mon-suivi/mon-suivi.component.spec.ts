import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { MonSuiviComponent } from './mon-suivi.component';

describe('MonSuiviComponent', () => {
  let component: MonSuiviComponent;
  let fixture: ComponentFixture<MonSuiviComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MonSuiviComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(MonSuiviComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});