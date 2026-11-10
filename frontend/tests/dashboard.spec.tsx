import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { expect, test } from 'vitest';
import { DashboardPage } from '../src/pages/DashboardPage';

test('dashboard informa indisponibilidade e oferece caminhos reais', () => {
 render(<MemoryRouter><DashboardPage/></MemoryRouter>);
 expect(screen.getByRole('status')).toHaveTextContent('integração');
 expect(screen.getByRole('link', {name:'Registrar consumo'})).toHaveAttribute('href','/consumos');
 expect(screen.getByRole('link', {name:'Consultar unidades'})).toHaveAttribute('href','/unidades');
 expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
});
