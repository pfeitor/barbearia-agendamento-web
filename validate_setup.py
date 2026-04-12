#!/usr/bin/env python3
"""
Script de validação do setup do projeto.
Verifica se todas as partes estão configuradas corretamente.
"""

import os
import sys
import django

# Configura Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

def validate_models():
    """Verifica se os models estão funcionando."""
    print("Validando models...")
    
    try:
        from apps.clientes.models import Cliente
        from apps.agendamentos.models import Agendamento
        from apps.core.mixins import ClienteRequiredMixin, AdminRequiredMixin
        from apps.core.backends import TelefoneBackend, AdminEmailBackend
        from apps.core.forms import ClienteLoginForm, AdminLoginForm
        print("Models e classes importados com sucesso!")
        return True
    except ImportError as e:
        print(f"Erro ao importar models: {e}")
        return False

def validate_urls():
    """Verifica se as URLs estão configuradas."""
    print("Validando URLs...")
    
    try:
        from django.urls import reverse
        from django.test import Client
        
        # Testar URLs principais
        urls_to_test = [
            'login_cliente',
            'login_admin', 
            'home',
            'admin_dashboard'
        ]
        
        client = Client()
        for url_name in urls_to_test:
            try:
                url = reverse(url_name)
                print(f"  {url_name}: {url}")
            except Exception as e:
                print(f"  {url_name}: ERRO - {e}")
                return False
        
        print("URLs validadas com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao validar URLs: {e}")
        return False

def create_test_data():
    """Cria dados de teste."""
    print("Criando dados de teste...")
    
    try:
        from django.contrib.auth import get_user_model
        from apps.clientes.models import Cliente
        from apps.profissionais.models import Profissional
        from apps.servicos.models import Servico
        from apps.agendamentos.models import Agendamento
        
        User = get_user_model()
        
        # Criar admin se não existir
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_user(
                username='admin',
                email='admin@barbearia.com',
                password='admin123',
                is_staff=True,
                is_superuser=True
            )
            print("  Admin criado: admin@barbearia.com / admin123")
        
        # Criar cliente se não existir
        if not Cliente.objects.filter(telefone='11999999999').exists():
            cliente = Cliente.objects.create(
                nome='João Teste',
                telefone='11999999999',
                email='joao@teste.com'
            )
            print("  Cliente criado: João Teste / 11999999999")
        
        # Criar profissional se não existir
        if not Profissional.objects.filter(nome='Carlos Barbearia').exists():
            profissional = Profissional.objects.create(
                nome='Carlos Barbearia',
                telefone='11777777777',
                email='carlos@barbearia.com'
            )
            print("  Profissional criado: Carlos Barbearia")
        
        # Criar serviço se não existir
        if not Servico.objects.filter(nome='Corte Masculino').exists():
            servico = Servico.objects.create(
                nome='Corte Masculino',
                preco=30.00,
                duracao_minutos=30
            )
            print("  Serviço criado: Corte Masculino")
        
        print("Dados de teste criados com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao criar dados de teste: {e}")
        return False

def test_basic_flows():
    """Testa fluxos básicos."""
    print("Testando fluxos básicos...")
    
    try:
        from django.test import Client
        
        client = Client()
        
        # Testar página inicial
        response = client.get('/')
        print(f"  Página inicial: {response.status_code}")
        
        # Testar login cliente
        response = client.get('/login-cliente/')
        print(f"  Login cliente: {response.status_code}")
        
        # Testar login admin
        response = client.get('/login-admin/')
        print(f"  Login admin: {response.status_code}")
        
        print("Fluxos básicos testados com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao testar fluxos: {e}")
        return False

def main():
    """Função principal."""
    print("=" * 60)
    print("Validação do Sistema de Autenticação Dual")
    print("=" * 60)
    
    validations = [
        ("Models e Classes", validate_models),
        ("URLs", validate_urls),
        ("Dados de Teste", create_test_data),
        ("Fluxos Básicos", test_basic_flows),
    ]
    
    all_passed = True
    
    for name, validator in validations:
        print(f"\n{name}:")
        if not validator():
            all_passed = False
            print(f"FALHA em {name}")
        else:
            print(f"OK em {name}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("VALIDAÇÃO CONCLUÍDA COM SUCESSO!")
        print("\nPróximos passos:")
        print("1. Acesse http://127.0.0.1:8000")
        print("2. Teste login cliente com telefone: 11999999999")
        print("3. Teste login admin com: admin@barbearia.com / admin123")
        print("4. Verifique se os menus aparecem corretamente")
    else:
        print("VALIDAÇÃO FALHOU! Verifique os erros acima.")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
