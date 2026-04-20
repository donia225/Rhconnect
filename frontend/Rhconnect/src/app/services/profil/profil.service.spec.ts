import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { ProfilService } from './profil.service';

describe('ProfilService', () => {
  let service: ProfilService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ProfilService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });

    service = TestBed.inject(ProfilService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});