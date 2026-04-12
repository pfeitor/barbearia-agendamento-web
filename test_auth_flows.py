#!/usr/bin/env python3
"""
Script de teste para validar os fluxos de autenticação implementados.
Execute: python test_auth_flows.py
"""

import os
import sys
import django

# Configura Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.clientes.models import Cliente
from apps.agendamentos.models import Agendamento
from apps.profissionais.models import Profissional
from apps.servicos.models import Servico

User = get_user_model()

class AuthFlowsTest(TestCase):
    def setUp(self):
        # Criar admin
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@barbearia.com',
            password='admin123',
            is_staff=True
        )
        
        # Criar cliente
        self.cliente = Cliente.objects.create(
            nome='João Silva',
            telefone='11999999999',
            email='joao@email.com'
        )
        
        # Criar outro cliente
        self.outro_cliente = Cliente.objects.create(
            nome='Maria Santos',
            telefone='11888888888',
            email='maria@email.com'
        )
        
        # Criar dados básicos para agendamentos
        self.profissional = Profissional.objects.create(
            nome='Carlos Barbearia',
            telefone='11777777777',
            email='carlos@barbearia.com'
        )
        
        self.servico = Servico.objects.create(
            nome='Corte Masculino',
            preco=30.00,
            duracao_minutos=30
        )
        
        # Criar agendamento do cliente
        self.agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            profissional=self.profissional,
            servico=self.servico,
            data_hora_inicio='2026-04-12 14:00:00'
        )
        
        # Criar agendamento do outro cliente
        self.outro_agendamento = Agendamento.objects.create(
            cliente=self.outro_cliente,
            profissional=self.profissional,
            servico=self.servico,
            data_hora_inicio='2026-04-12 15:00:00'
        )

def test_login_cliente_telefone_existente(self):
    """Testa login de cliente com telefone existente."""
    client = Client()
    
    # Acessar página inicial
    response = client.get('/')
    self.assertEqual(response.status_code, 302)  # Redireciona para login
    
    # Fazer login
    response = client.post('/login-cliente/', {
        'telefone': '11999999999'
    })
    
    # Verificar se autenticou
    self.assertEqual(response.status_code, 302)
    self.assertIn('cliente_id', client.session)
    self.assertEqual(client.session['cliente_id'], self.cliente.id)

def test_login_cliente_telefone_inexistente(self):
    """Testa login de cliente com telefone inexistente."""
    client = Client()
    
    # Tentar login com telefone inexistente
    response = client.post('/login-cliente/', {
        'telefone': '11111111111'
    })
    
    # Deve redirecionar para cadastro
    self.assertEqual(response.status_code, 302)
    self.assertIn('telefone_cadastro', client.session)
    self.assertEqual(client.session['telefone_cadastro'], '11111111111')

def test_login_admin_sucesso(self):
    """Testa login de administrador."""
    client = Client()
    
    # Fazer login admin
    response = client.post('/login-admin/', {
        'email': 'admin@barbearia.com',
        'password': 'admin123'
    })
    
    # Verificar se autenticou
    self.assertEqual(response.status_code, 302)
    self.assertTrue(response.wsgi_request.user.is_authenticated)
    self.assertTrue(response.wsgi_request.user.is_staff)

def test_login_admin_falha(self):
    """Testa login de administrador com credenciais erradas."""
    client = Client()
    
    # Tentar login com senha errada
    response = client.post('/login-admin/', {
        'email': 'admin@barbearia.com',
        'password': 'senha_errada'
    })
    
    # Deve retornar erro
    self.assertEqual(response.status_code, 200)
    self.assertFalse(response.wsgi_request.user.is_authenticated)

def test_cliente_acesso_admin_negado(self):
    """Testa se cliente não pode acessar área admin."""
    client = Client()
    
    # Autenticar cliente
    client.post('/login-cliente/', {'telefone': '11999999999'})
    
    # Tentar acessar painel admin
    response = client.get('/painel/')
    self.assertEqual(response.status_code, 403)
    
    # Tentar acessar lista de clientes
    response = client.get('/clientes/')
    self.assertEqual(response.status_code, 403)

def test_cliente_so_ve_seus_agendamentos(self):
    """Testa se cliente só vê seus próprios agendamentos."""
    client = Client()
    
    # Autenticar cliente
    client.post('/login-cliente/', {'telefone': '11999999999'})
    
    # Acessar meus agendamentos
    response = client.get('/agendamentos/meus-agendamentos/')
    self.assertEqual(response.status_code, 200)
    
    # Verificar se só mostra agendamento do cliente
    agendamentos = response.context['agendamentos']
    self.assertEqual(len(agendamentos), 1)
    self.assertEqual(agendamentos[0].cliente, self.cliente)

def test_cliente_tentando_ver_agendamento_alheio(self):
    """Testa se cliente não pode ver agendamento de outro cliente."""
    client = Client()
    
    # Autenticar cliente
    client.post('/login-cliente/', {'telefone': '11999999999'})
    
    # Tentar editar agendamento de outro cliente
    response = client.get(f'/agendamentos/{self.outro_agendamento.id}/editar/')
    self.assertEqual(response.status_code, 404)  # Não encontrado (queryset filtrado)

def test_admin_acesso_total(self):
    """Testa se admin tem acesso total."""
    client = Client()
    
    # Autenticar admin
    client.post('/login-admin/', {
        'email': 'admin@barbearia.com',
        'password': 'admin123'
    })
    
    # Acessar painel admin
    response = client.get('/painel/')
    self.assertEqual(response.status_code, 200)
    
    # Acessar lista de clientes
    response = client.get('/clientes/')
    self.assertEqual(response.status_code, 200)
    
    # Verificar se vê todos os agendamentos
    response = client.get('/agendamentos/')
    self.assertEqual(response.status_code, 200)
    agendamentos = response.context['agendamentos']
    self.assertEqual(len(agendamentos), 2)  # Todos os agendamentos

def run_tests():
    """Executa todos os testes."""
    import django
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2)
    
    # Criar instância de teste
    test_instance = AuthFlowsTest()
    test_instance.setUp()
    
    # Executar testes individuais
    tests = [
        test_instance.test_login_cliente_telefone_existente,
        test_instance.test_login_cliente_telefone_inexistente,
        test_instance.test_login_admin_sucesso,
        test_instance.test_login_admin_falha,
        test_instance.test_cliente_acesso_admin_negado,
        test_instance.test_cliente_so_ve_seus_agendamentos,
        test_instance.test_cliente_tentando_ver_agendamento_alheio,
        test_instance.test_admin_acesso_total,
    ]
    
    print("Executando testes dos fluxos de autenticação...")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {test.__name__} - {str(e)}")
            failed += 1
    
    print("=" * 60)
    print(f"Resultados: {passed} passaram, {failed} falharam")
    
    if failed == 0:
        print("Todos os testes passaram! Sistema funcionando corretamente.")
    else:
        print("Alguns testes falharam. Verifique os erros acima.")

if __name__ == '__main__':
    run_tests()
