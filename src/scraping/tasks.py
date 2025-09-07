from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import Course, Assignment
from user.models import UnaerpCredentials
from .unaerp_scraper import UnaerpScraper, CredentialsManager
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True)
def scrape_user_data(self, user_id):
    """
    Tarefa assíncrona para fazer scraping dos dados de um usuário específico

    Args:
        user_id (int): ID do usuário para fazer scraping
    """
    try:
        # Buscar usuário
        user = User.objects.get(id=user_id)

        # Verificar se o usuário tem credenciais UNAERP
        if not hasattr(user, 'unaerp_credentials'):
            logger.error(f"Usuário {user.email} não possui credenciais UNAERP")
            return {
                'success': False,
                'error': 'Credenciais UNAERP não encontradas'
            }

        credentials = user.unaerp_credentials

        # Descriptografar senha
        try:
            decrypted_password = CredentialsManager.decrypt_password(credentials.encrypted_password)
        except Exception as e:
            logger.error(f"Erro ao descriptografar senha para usuário {user.email}: {str(e)}")
            return {
                'success': False,
                'error': 'Erro ao acessar credenciais'
            }

        # Inicializar scraper
        scraper = UnaerpScraper(credentials.ra, decrypted_password)

        # Executar scraping
        scraping_result = scraper.scrape_all_data()

        if not scraping_result['success']:
            logger.error(f"Falha no scraping para usuário {user.email}: {scraping_result.get('error', 'Erro desconhecido')}")
            return scraping_result

        # Processar dados extraídos
        courses_created = 0
        assignments_created = 0

        for course_data in scraping_result['courses']:
            # Criar ou atualizar disciplina
            course, created = Course.objects.get_or_create(
                user=user,
                name=course_data['name'],
                defaults={
                    'instructor': course_data.get('instructor', ''),
                }
            )

            if created:
                courses_created += 1
                logger.info(f"Disciplina criada: {course.name} para usuário {user.email}")

            # Processar atividades da disciplina
            for assignment_data in course_data.get('assignments', []):
                assignment, created = Assignment.objects.get_or_create(
                    user=user,
                    course=course,
                    title=assignment_data['title'],
                    defaults={
                        'due_date': assignment_data.get('due_date'),
                        'completed': False,
                    }
                )

                if created:
                    assignments_created += 1
                    logger.info(f"Atividade criada: {assignment.title} para disciplina {course.name}")

        # Atualizar timestamp do último scraping
        credentials.last_sync = timezone.now()
        credentials.save()

        # Fechar scraper
        scraper.close()

        result = {
            'success': True,
            'courses_created': courses_created,
            'assignments_created': assignments_created,
            'total_courses': len(scraping_result['courses']),
            'total_assignments': scraping_result['assignments_count']
        }

        logger.info(f"Scraping concluído para usuário {user.email}: {result}")
        return result

    except User.DoesNotExist:
        logger.error(f"Usuário com ID {user_id} não encontrado")
        return {
            'success': False,
            'error': 'Usuário não encontrado'
        }
    except Exception as e:
        logger.error(f"Erro inesperado no scraping para usuário ID {user_id}: {str(e)}")
        return {
            'success': False,
            'error': f'Erro inesperado: {str(e)}'
        }


@shared_task
def scrape_all_users():
    """
    Tarefa assíncrona para fazer scraping de todos os usuários com credenciais UNAERP
    """
    try:
        # Buscar todos os usuários com credenciais UNAERP
        users_with_credentials = User.objects.filter(unaerp_credentials__isnull=False)

        results = []

        for user in users_with_credentials:
            logger.info(f"Iniciando scraping para usuário {user.email}")

            # Executar scraping para o usuário
            result = scrape_user_data.delay(user.id)
            results.append({
                'user_id': user.id,
                'user_email': user.email,
                'task_id': result.id
            })

        logger.info(f"Scraping iniciado para {len(results)} usuários")
        return {
            'success': True,
            'users_processed': len(results),
            'tasks': results
        }

    except Exception as e:
        logger.error(f"Erro ao executar scraping para todos os usuários: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def periodic_scraping():
    """
    Tarefa periódica para executar scraping automaticamente
    """
    logger.info("Iniciando scraping periódico")
    return scrape_all_users()
