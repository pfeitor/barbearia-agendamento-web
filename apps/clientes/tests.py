from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from .models import Cliente, ClienteUser, VerificacaoEmail
from .services import AuthService


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def make_user(email='teste@example.com', password='Senha123', is_active=True, is_staff=False):
    return ClienteUser.objects.create_user(email=email, password=password, is_active=is_active, is_staff=is_staff)


def make_cliente(user, nome='João', telefone='11999990000'):
    return Cliente.objects.create(nome=nome, telefone=telefone, email=user.email, cliente_user=user)


# ─── Model: ClienteUser ───────────────────────────────────────────────────────

class ClienteUserModelTest(TestCase):
    def test_create_user_salva_email(self):
        u = make_user()
        self.assertEqual(u.email, 'teste@example.com')

    def test_is_active_false_por_padrao(self):
        u = ClienteUser.objects.create_user(email='novo@x.com', password='Abc12345')
        self.assertFalse(u.is_active)

    def test_create_superuser_is_active_true(self):
        su = ClienteUser.objects.create_superuser(email='admin@x.com', password='Admin123')
        self.assertTrue(su.is_active)
        self.assertTrue(su.is_staff)
        self.assertTrue(su.is_superuser)

    def test_str_retorna_email(self):
        u = make_user()
        self.assertEqual(str(u), 'teste@example.com')


# ─── Model: VerificacaoEmail ──────────────────────────────────────────────────

class VerificacaoEmailModelTest(TestCase):
    def setUp(self):
        self.user = make_user(is_active=False)

    def test_is_valid_codigo_ativo(self):
        v = VerificacaoEmail.objects.create(
            cliente_user=self.user,
            code='123456',
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        self.assertTrue(v.is_valid())

    def test_is_valid_codigo_expirado(self):
        v = VerificacaoEmail.objects.create(
            cliente_user=self.user,
            code='123456',
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        self.assertFalse(v.is_valid())

    def test_is_valid_codigo_usado(self):
        v = VerificacaoEmail.objects.create(
            cliente_user=self.user,
            code='123456',
            expires_at=timezone.now() + timedelta(minutes=10),
            is_used=True,
        )
        self.assertFalse(v.is_valid())


# ─── Service: AuthService.verificar_codigo ────────────────────────────────────

class AuthServiceVerificarCodigoTest(TestCase):
    def setUp(self):
        self.user = make_user(is_active=False)
        self.verificacao = VerificacaoEmail.objects.create(
            cliente_user=self.user,
            code='654321',
            expires_at=timezone.now() + timedelta(minutes=15),
        )

    def test_codigo_correto_ativa_usuario(self):
        resultado = AuthService.verificar_codigo(self.user, '654321')
        self.assertTrue(resultado)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_codigo_errado_nao_ativa(self):
        resultado = AuthService.verificar_codigo(self.user, '000000')
        self.assertFalse(resultado)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_codigo_expirado_nao_ativa(self):
        self.verificacao.expires_at = timezone.now() - timedelta(minutes=1)
        self.verificacao.save()
        resultado = AuthService.verificar_codigo(self.user, '654321')
        self.assertFalse(resultado)

    def test_codigo_ja_usado_nao_ativa(self):
        self.verificacao.is_used = True
        self.verificacao.save()
        resultado = AuthService.verificar_codigo(self.user, '654321')
        self.assertFalse(resultado)


# ─── Service: rate limit ──────────────────────────────────────────────────────

class AuthServiceRateLimitTest(TestCase):
    def setUp(self):
        self.user = make_user(is_active=False)

    def _criar_verificacoes(self, n):
        for i in range(n):
            VerificacaoEmail.objects.create(
                cliente_user=self.user,
                code=f'{i:06d}',
                expires_at=timezone.now() + timedelta(minutes=15),
                created_at=timezone.now(),
            )

    def test_rate_limit_levanta_value_error(self):
        self._criar_verificacoes(3)
        with self.assertRaises(ValueError):
            AuthService.gerar_e_enviar_codigo(self.user)


# ─── Service: validar_token_reset ────────────────────────────────────────────

class AuthServiceResetTokenTest(TestCase):
    def test_token_invalido_retorna_none(self):
        resultado = AuthService.validar_token_reset('invalido', 'token_errado')
        self.assertIsNone(resultado)


# ─── View: Registro ───────────────────────────────────────────────────────────

class ClienteRegisterViewTest(TestCase):
    def test_get_renderiza_formulario(self):
        resp = self.client.get(reverse('clientes_registrar'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Criar conta')

    def test_email_duplicado_exibe_erro(self):
        make_user(email='dup@x.com')
        resp = self.client.post(reverse('clientes_registrar'), {
            'nome': 'Dup',
            'telefone': '11900000001',
            'email': 'dup@x.com',
            'senha': 'Senha123',
            'confirmar_senha': 'Senha123',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'já está cadastrado')

    def test_senhas_diferentes_exibe_erro(self):
        resp = self.client.post(reverse('clientes_registrar'), {
            'nome': 'Teste',
            'telefone': '11900000002',
            'email': 'novo@x.com',
            'senha': 'Senha123',
            'confirmar_senha': 'Outra999',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'não coincidem')

    def test_senha_fraca_sem_maiuscula(self):
        resp = self.client.post(reverse('clientes_registrar'), {
            'nome': 'Fraco',
            'telefone': '11900000003',
            'email': 'fraco@x.com',
            'senha': 'sem123456',
            'confirmar_senha': 'sem123456',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'maiúscula')


# ─── View: Login ──────────────────────────────────────────────────────────────

class ClienteLoginViewTest(TestCase):
    def setUp(self):
        self.user = make_user(email='login@x.com', password='Senha123', is_active=True)
        make_cliente(self.user)

    def test_get_exibe_formulario(self):
        resp = self.client.get(reverse('clientes_login'))
        self.assertEqual(resp.status_code, 200)

    def test_login_valido_redireciona_home(self):
        resp = self.client.post(reverse('clientes_login'), {
            'email': 'login@x.com',
            'senha': 'Senha123',
        })
        self.assertRedirects(resp, reverse('home'), fetch_redirect_response=False)

    def test_login_invalido_exibe_erro(self):
        resp = self.client.post(reverse('clientes_login'), {
            'email': 'login@x.com',
            'senha': 'errada',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'inválidos')

    def test_usuario_inativo_vai_para_verificacao(self):
        inativo = make_user(email='inativo@x.com', password='Senha123', is_active=False)
        resp = self.client.post(reverse('clientes_login'), {
            'email': 'inativo@x.com',
            'senha': 'Senha123',
        })
        self.assertRedirects(resp, reverse('verificar_email'), fetch_redirect_response=False)
        self.assertEqual(self.client.session.get('verificacao_user_id'), inativo.pk)


# ─── View: Verificar e-mail ───────────────────────────────────────────────────

class VerificarEmailViewTest(TestCase):
    def setUp(self):
        self.user = make_user(email='verif@x.com', password='Senha123', is_active=False)
        session = self.client.session
        session['verificacao_user_id'] = self.user.pk
        session.save()

    def test_sem_sessao_redireciona_login(self):
        c = Client()
        resp = c.get(reverse('verificar_email'))
        self.assertRedirects(resp, reverse('clientes_login'), fetch_redirect_response=False)

    def test_codigo_invalido_mantem_pagina(self):
        resp = self.client.post(reverse('verificar_email'), {'codigo': '000000'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'inválido')

    def test_codigo_valido_autentica_e_redireciona(self):
        VerificacaoEmail.objects.create(
            cliente_user=self.user,
            code='111111',
            expires_at=timezone.now() + timedelta(minutes=15),
        )
        resp = self.client.post(reverse('verificar_email'), {'codigo': '111111'})
        self.assertRedirects(resp, reverse('home'), fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)


# ─── View: Esqueci senha ──────────────────────────────────────────────────────

class EsqueciSenhaViewTest(TestCase):
    def test_get_renderiza_formulario(self):
        resp = self.client.get(reverse('esqueci_senha'))
        self.assertEqual(resp.status_code, 200)

    def test_email_inexistente_nao_vaza_info(self):
        resp = self.client.post(reverse('esqueci_senha'), {'email': 'naoexiste@x.com'})
        self.assertRedirects(resp, reverse('clientes_login'), fetch_redirect_response=False)


# ─── View: ClienteRequiredMixin ───────────────────────────────────────────────

class ClienteRequiredMixinTest(TestCase):
    def test_anonimo_redireciona_login(self):
        resp = self.client.get(reverse('meus_agendamentos'))
        self.assertIn(resp.status_code, [301, 302])

    def test_cliente_autenticado_acessa(self):
        user = make_user(email='ok@x.com', password='Senha123', is_active=True)
        make_cliente(user)
        self.client.force_login(user)
        resp = self.client.get(reverse('meus_agendamentos'))
        self.assertEqual(resp.status_code, 200)

    def test_admin_sem_perfil_nao_acessa_area_cliente(self):
        admin = ClienteUser.objects.create_superuser(email='adm@x.com', password='Admin123')
        self.client.force_login(admin)
        resp = self.client.get(reverse('meus_agendamentos'))
        self.assertIn(resp.status_code, [301, 302])
