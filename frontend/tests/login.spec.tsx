import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test, vi } from 'vitest';
import { Login } from '../src/components/Login';
import { signInWithEmailAndPassword } from 'firebase/auth';
vi.mock('../src/auth',()=>({auth:{}}));
vi.mock('firebase/auth',()=>({signInWithEmailAndPassword:vi.fn()}));
test('login funciona com teclado e mantém erro compreensível',async()=>{
 vi.mocked(signInWithEmailAndPassword).mockRejectedValue(new Error('offline'));
 const user=userEvent.setup(); render(<Login/>);
 await user.tab(); expect(screen.getByLabelText('E-mail')).toHaveFocus();
 await user.keyboard('funcionario@example.test'); await user.tab(); expect(screen.getByLabelText('Senha')).toHaveFocus();
 await user.keyboard('senha-temporaria'); await user.tab(); expect(screen.getByRole('button',{name:'Entrar'})).toHaveFocus();
 await user.keyboard('{Enter}'); expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível entrar');
 expect(signInWithEmailAndPassword).toHaveBeenCalledTimes(1);
});
