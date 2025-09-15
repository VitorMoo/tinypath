import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, date
from typing import List, Dict, Optional
from urllib.parse import urljoin
import logging
from cryptography.fernet import Fernet
from django.conf import settings

logger = logging.getLogger(__name__)


class UnaerpScraper:
    """
    Scraper para o sistema UNAERP
    """

    BASE_URL = "https://ead.unaerp.br"
    LOGIN_URL = f"{BASE_URL}/login/index.php"
    DASHBOARD_URL = f"{BASE_URL}/my/"

    def __init__(self, ra: str, password: str):
        """
        Inicializa o scraper com as credenciais do usuário

        Args:
            ra (str): RA do estudante (usado como username)
            password (str): Senha do estudante
        """
        self.username = ra
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def login(self) -> bool:
        """
        Realiza login no sistema Moodle da UNAERP

        Returns:
            bool: True se o login foi bem-sucedido, False caso contrário
        """
        try:
            logger.info(f"Iniciando processo de login para usuário: {self.username}")

            # Primeira requisição para obter o logintoken
            response = self.session.get(self.LOGIN_URL)
            response.raise_for_status()

            logger.info(f"Página de login acessada. Status: {response.status_code}")
            logger.info(f"URL final: {response.url}")

            soup = BeautifulSoup(response.content, 'html.parser')
            logintoken = soup.find('input', {'name': 'logintoken'})

            if not logintoken:
                logger.error("Não foi possível encontrar o 'logintoken' na página de login.")
                # Vamos verificar se há outros tokens ou se a estrutura mudou
                logger.info("Buscando por outros tipos de token...")
                all_inputs = soup.find_all('input', {'type': 'hidden'})
                for inp in all_inputs:
                    logger.info(f"Input hidden encontrado: {inp.get('name')} = {inp.get('value')}")
                return False

            logintoken = logintoken.get('value')
            logger.info(f"Logintoken obtido: {logintoken[:10]}...")

            # Dados do login para Moodle
            login_data = {
                'username': self.username,
                'password': self.password,
                'logintoken': logintoken,
                'anchor': ''
            }

            logger.info(f"Dados de login preparados para usuário: {self.username}")

            # Realizar login
            response = self.session.post(self.LOGIN_URL, data=login_data)
            response.raise_for_status()

            logger.info(f"POST de login realizado. Status: {response.status_code}")
            logger.info(f"URL após login: {response.url}")

            # Verificar se o login foi bem-sucedido
            if self.DASHBOARD_URL in response.url or 'login/logout.php' in response.text:
                logger.info(f"Login realizado com sucesso para usuário: {self.username}")
                return True
            else:
                logger.error(f"Falha no login para usuário: {self.username}. A URL final é {response.url}")
                # Verificar se há mensagem de erro
                soup = BeautifulSoup(response.content, 'html.parser')
                error_message = soup.find('div', {'class': 'alert-danger'})
                if error_message:
                    logger.error(f"Mensagem de erro: {error_message.get_text(strip=True)}")

                # Vamos verificar se ainda estamos na página de login
                if 'login/index.php' in response.url:
                    logger.error("Ainda na página de login após tentativa - credenciais inválidas ou erro no processo")
                    # Verificar por mensagens de erro específicas
                    error_elements = soup.find_all(['div', 'span'], class_=['error', 'alert', 'notification'])
                    for elem in error_elements:
                        if elem.get_text(strip=True):
                            logger.error(f"Erro encontrado: {elem.get_text(strip=True)}")

                return False

        except requests.RequestException as e:
            logger.error(f"Erro na requisição de login: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado no login: {str(e)}")
            return False
            logger.error(f"Erro inesperado no login: {str(e)}")
            return False

    def get_courses(self) -> List[Dict]:
        """
        Extrai lista de disciplinas do dashboard do Moodle

        Returns:
            List[Dict]: Lista de disciplinas com informações
        """
        try:
            response = self.session.get(self.DASHBOARD_URL)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            courses = []

            # Buscar disciplinas no menu lateral (nav-drawer)
            nav_drawer = soup.find('div', {'id': 'nav-drawer'})
            if nav_drawer:
                # Procurar por links de disciplinas dentro da seção "Minhas disciplinas"
                course_links = nav_drawer.find_all('a', href=lambda x: x and 'course/view.php?id=' in x)

                for link in course_links:
                    try:
                        course_name = link.find('span', class_='media-body')
                        if course_name:
                            name_text = course_name.get_text(strip=True)
                            # Filtrar apenas disciplinas reais (não "Minhas disciplinas")
                            if name_text and name_text != 'Minhas disciplinas':
                                course_data = {
                                    'name': name_text,
                                    'instructor': 'N/A',
                                    'link': link.get('href'),
                                }
                                courses.append(course_data)
                    except Exception as e:
                        logger.warning(f"Erro ao processar link de disciplina: {str(e)}")
                        continue

            # Se não encontrou no nav-drawer, tentar no dropdown menu
            if not courses:
                dropdown_menu = soup.find('div', class_='dropdown-menu')
                if dropdown_menu:
                    course_links = dropdown_menu.find_all('a', href=lambda x: x and 'course/view.php?id=' in x)

                    for link in course_links:
                        try:
                            name_text = link.get_text(strip=True)
                            if name_text:
                                course_data = {
                                    'name': name_text,
                                    'instructor': 'N/A',
                                    'link': link.get('href'),
                                }
                                courses.append(course_data)
                        except Exception as e:
                            logger.warning(f"Erro ao processar disciplina do dropdown: {str(e)}")
                            continue

            logger.info(f"Encontradas {len(courses)} disciplinas para usuário: {self.username}")
            return courses

        except requests.RequestException as e:
            logger.error(f"Erro ao buscar disciplinas: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar disciplinas: {str(e)}")
            return []

    def get_assignments(self, course_url: str) -> List[Dict]:
        """
        Extrai atividades de uma disciplina específica do Moodle UNAERP

        O Moodle da UNAERP organiza atividades em UNIDADES que devem ser acessadas individualmente.
        Cada unidade contém tarefas e questionários específicos.

        Args:
            course_url (str): URL da disciplina

        Returns:
            List[Dict]: Lista de atividades com informações
        """
        try:
            logger.info(f"Buscando atividades na URL: {course_url}")
            response = self.session.get(course_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            assignments = []

            # Log da estrutura da página para debug
            logger.info(f"Título da página: {soup.title.string if soup.title else 'N/A'}")

            # Verificar se a página carregou corretamente
            if 'login' in response.url.lower():
                logger.error("Redirecionado para login - sessão pode ter expirado")
                return []

            # ESTRATÉGIA ESPECÍFICA PARA UNAERP: Buscar por unidades (tiles) e acessar cada uma

            # 1. Encontrar todos os tiles das unidades
            unit_tiles = soup.select('li.tile.tile-clickable[data-section]')
            logger.info(f"Encontrados {len(unit_tiles)} tiles de unidades")

            # 2. Extrair informações das unidades dos tooltips
            for tile in unit_tiles:
                try:
                    # Extrair número da seção
                    section_num = tile.get('data-section')
                    if not section_num or section_num == '0':  # Pular seção 0 (cabeçalho)
                        continue

                    # Buscar informações no tooltip
                    tile_text_elem = tile.select_one('[data-original-title]')
                    if tile_text_elem:
                        tooltip_content = tile_text_elem.get('data-original-title', '')
                        logger.debug(f"Tooltip da seção {section_num}: {tooltip_content}")

                        # Extrair nome da unidade
                        unit_name_elem = tile.select_one('.photo-tile-text h3, .tile-text h3')
                        unit_name = unit_name_elem.get_text(strip=True) if unit_name_elem else f"Unidade {section_num}"

                        # Verificar se há tarefas ou questionários no tooltip
                        has_assignments = ('Tarefa:' in tooltip_content or
                                         'Questionário:' in tooltip_content or
                                         'tarefa' in tooltip_content.lower() or
                                         'questionário' in tooltip_content.lower())

                        if has_assignments:
                            logger.info(f"Unidade {section_num} ({unit_name}) contém atividades, acessando...")

                            # Construir URL da seção específica
                            section_url = f"{course_url}&section={section_num}"

                            # Acessar a seção para extrair atividades
                            section_assignments = self._extract_assignments_from_section(section_url, unit_name, section_num)
                            assignments.extend(section_assignments)
                        else:
                            logger.debug(f"Unidade {section_num} ({unit_name}) não contém atividades avaliativas")

                except Exception as e:
                    logger.error(f"Erro ao processar tile da unidade: {e}")
                    continue

            # 3. FALLBACK: Buscar atividades na página principal (como antes)
            if not assignments:
                logger.info("Nenhuma atividade encontrada nas unidades, tentando busca na página principal...")
                assignments = self._extract_assignments_from_main_page(soup, course_url)

            logger.info(f"Total de {len(assignments)} atividades encontradas em {course_url}")
            for assignment in assignments:
                logger.debug(f"  - {assignment['title']} ({assignment['type']})")

            return assignments

        except requests.RequestException as e:
            logger.error(f"Erro ao buscar atividades: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar atividades: {str(e)}")
            return []

    def _extract_assignments_from_section(self, section_url: str, unit_name: str, section_num: str) -> List[Dict]:
        """
        Extrai atividades de uma seção/unidade específica

        Args:
            section_url (str): URL da seção
            unit_name (str): Nome da unidade
            section_num (str): Número da seção

        Returns:
            List[Dict]: Lista de atividades da seção
        """
        try:
            logger.debug(f"Acessando seção: {section_url}")
            response = self.session.get(section_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            assignments = []

            # Buscar por atividades específicas dentro da seção
            # Procurar por links de módulos que sejam tarefas ou questionários
            activity_selectors = [
                'a[href*="mod/assign"]',  # Tarefas
                'a[href*="mod/quiz"]',    # Questionários
                'a[href*="mod/workshop"]', # Workshops
                'a[href*="mod/feedback"]', # Feedbacks
                'li.activity.assign',
                'li.activity.quiz',
                'li.activity.workshop',
                '.modtype_assign',
                '.modtype_quiz',
                '.modtype_workshop'
            ]

            found_activities = set()  # Para evitar duplicatas

            for selector in activity_selectors:
                elements = soup.select(selector)
                logger.debug(f"Seção {section_num} - Selector '{selector}': {len(elements)} elementos")

                for element in elements:
                    try:
                        # Extrair URL da atividade
                        if element.name == 'a':
                            activity_url = element.get('href')
                            link_element = element
                        else:
                            link_element = element.select_one('a[href*="mod/"]')
                            activity_url = link_element.get('href') if link_element else None

                        if not activity_url:
                            continue

                        # Converter para URL absoluta
                        if not activity_url.startswith('http'):
                            activity_url = urljoin(section_url, activity_url)

                        # Evitar duplicatas
                        if activity_url in found_activities:
                            continue
                        found_activities.add(activity_url)

                        # Extrair título da atividade
                        title = self._extract_activity_title(element, link_element)

                        if not title or len(title.strip()) < 3:
                            continue

                        # Filtrar atividades que devem ser ignoradas
                        title_lower = title.lower().strip()
                        if ('envio de tarefa fora do prazo' in title_lower or
                            'envio de tarefa fora de prazo' in title_lower or
                            'fora do prazo' in title_lower):
                            logger.debug(f"Ignorando atividade: {title}")
                            continue

                        # Determinar tipo da atividade
                        activity_type = 'assignment'
                        if 'mod/quiz' in activity_url:
                            activity_type = 'quiz'
                        elif 'mod/assign' in activity_url:
                            activity_type = 'assignment'
                        elif 'mod/workshop' in activity_url:
                            activity_type = 'workshop'
                        elif 'mod/feedback' in activity_url:
                            activity_type = 'feedback'

                        # Criar objeto da atividade
                        assignment = {
                            'title': title.strip(),
                            'url': activity_url,
                            'due_date': None,  # Será extraído da página da atividade
                            'type': activity_type,
                            'course_url': section_url,
                            'unit_name': unit_name,
                            'unit_number': section_num
                        }

                        # Extrair data de vencimento acessando a página da atividade
                        due_date = self._extract_due_date_from_activity(activity_url)
                        if due_date:
                            assignment['due_date'] = due_date

                        assignments.append(assignment)
                        logger.info(f"Atividade encontrada na {unit_name}: {title} ({activity_type}) - Prazo: {due_date or 'Não definido'}")

                    except Exception as e:
                        logger.debug(f"Erro ao processar elemento de atividade: {e}")
                        continue

            # Se não encontrou atividades com seletores específicos, buscar de forma mais ampla
            if not assignments:
                logger.debug(f"Tentando busca ampla na seção {section_num}")

                # Buscar por qualquer link que pareça ser uma atividade
                all_links = soup.select('a[href*="mod/"]')
                for link in all_links:
                    try:
                        href = link.get('href')
                        if not href:
                            continue

                        # Filtrar apenas atividades relevantes
                        if any(mod in href for mod in ['assign', 'quiz', 'workshop', 'feedback']):
                            if not href.startswith('http'):
                                href = urljoin(section_url, href)

                            if href in found_activities:
                                continue
                            found_activities.add(href)

                            title = link.get_text(strip=True)
                            if title and len(title) > 3:
                                # Filtrar atividades que devem ser ignoradas
                                title_lower = title.lower().strip()
                                if ('envio de tarefa fora do prazo' in title_lower or
                                    'envio de tarefa fora de prazo' in title_lower or
                                    'fora do prazo' in title_lower):
                                    logger.debug(f"Ignorando atividade (busca ampla): {title}")
                                    continue

                                activity_type = 'assignment'
                                if 'quiz' in href:
                                    activity_type = 'quiz'
                                elif 'workshop' in href:
                                    activity_type = 'workshop'

                                assignment = {
                                    'title': title.strip(),
                                    'url': href,
                                    'due_date': None,
                                    'type': activity_type,
                                    'course_url': section_url,
                                    'unit_name': unit_name,
                                    'unit_number': section_num
                                }

                                # Extrair data de vencimento acessando a página da atividade
                                due_date = self._extract_due_date_from_activity(href)
                                if due_date:
                                    assignment['due_date'] = due_date

                                assignments.append(assignment)
                                logger.info(f"Atividade encontrada (busca ampla) na {unit_name}: {title} ({activity_type}) - Prazo: {due_date or 'Não definido'}")
                    except Exception as e:
                        logger.debug(f"Erro na busca ampla: {e}")
                        continue

            return assignments

        except Exception as e:
            logger.error(f"Erro ao extrair atividades da seção {section_num}: {e}")
            return []

    def _extract_activity_title(self, element, link_element) -> str:
        """
        Extrai o título de uma atividade de diferentes formas

        Args:
            element: Elemento principal
            link_element: Elemento de link

        Returns:
            str: Título da atividade
        """
        # Tentar diferentes formas de extrair o título
        title_selectors = [
            '.instancename',
            '.activityname',
            'span.instancename',
            '.activity-title'
        ]

        # 1. Buscar em elementos específicos
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) > 2:
                    return title

        # 2. Buscar no link
        if link_element:
            title = link_element.get_text(strip=True)
            if title and len(title) > 2:
                return title

            # Buscar em atributos
            title = link_element.get('title') or link_element.get('aria-label')
            if title and len(title) > 2:
                return title

        # 3. Buscar no elemento principal
        title = element.get_text(strip=True)
        if title and len(title) > 2:
            # Pegar apenas a primeira linha
            lines = [line.strip() for line in title.split('\n') if line.strip()]
            if lines:
                return lines[0]

        return "Atividade sem nome"

    def _extract_due_date_from_activity(self, activity_url: str) -> Optional[date]:
        """
        Extrai a data de vencimento acessando a página específica da atividade

        Args:
            activity_url (str): URL da atividade

        Returns:
            Optional[date]: Data de vencimento extraída da tabela de informações da atividade ou seção de questionário
        """
        try:
            logger.debug(f"Extraindo data de vencimento de: {activity_url}")

            response = self.session.get(activity_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # ESTRATÉGIA ESPECÍFICA PARA QUESTIONÁRIOS"
            if 'mod/quiz' in activity_url:

                # Buscar em divs com classe "box quizinfo"
                quiz_info_boxes = soup.find_all('div', class_='box quizinfo')
                for box in quiz_info_boxes:
                    box_text = box.get_text()

                    # Procurar por parágrafo que contém "será fechado em"
                    close_paragraphs = box.find_all('p', string=lambda text: text and 'será fechado em' in text)
                    for p in close_paragraphs:
                        date_text = p.get_text(strip=True)

                        # Extrair apenas a parte da data (após "será fechado em")
                        if 'será fechado em' in date_text:
                            date_part = date_text.split('será fechado em')[-1].strip()
                            logger.debug(f"Parte da data extraída: {date_part}")

                            parsed_date = self._parse_due_date(date_part)
                            if parsed_date:
                                logger.info(f"Data de fechamento do questionário extraída: {parsed_date}")
                                return parsed_date

                # Buscar também em texto geral para questionários
                quiz_close_text = soup.find(string=re.compile(r'será fechado em', re.IGNORECASE))
                if quiz_close_text:
                    full_text = quiz_close_text.strip()

                    if 'será fechado em' in full_text:
                        date_part = full_text.split('será fechado em')[-1].strip()
                        parsed_date = self._parse_due_date(date_part)
                        if parsed_date:
                            logger.info(f"Data de fechamento do questionário extraída: {parsed_date}")
                            return parsed_date

            # ESTRATÉGIA PRINCIPAL: Buscar na tabela por "Data de entrega" (para tarefas)
            # Procurar por todas as células da tabela que contenham "Data de entrega"
            table_cells = soup.find_all('td', string=lambda text: text and 'Data de entrega' in text)

            for cell in table_cells:
                logger.debug(f"Encontrada célula 'Data de entrega': {cell.get_text(strip=True)}")

                # Buscar a célula seguinte (mesmo tr, próxima td)
                next_cell = cell.find_next_sibling('td')
                if next_cell:
                    date_text = next_cell.get_text(strip=True)
                    logger.debug(f"Data encontrada na célula seguinte: {date_text}")

                    # Tentar extrair a data do texto
                    parsed_date = self._parse_due_date(date_text)
                    if parsed_date:
                        logger.info(f"Data de entrega extraída com sucesso: {parsed_date}")
                        return parsed_date

            # ESTRATÉGIA ALTERNATIVA 1: Buscar em qualquer tr que contenha "Data de entrega"
            table_rows = soup.find_all('tr')
            for row in table_rows:
                row_text = row.get_text()
                if 'Data de entrega' in row_text:
                    logger.debug(f"Linha com 'Data de entrega' encontrada: {row_text}")

                    # Buscar todas as células da linha
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        # Procurar a célula que contém a data (normalmente a segunda)
                        for i, cell in enumerate(cells):
                            if 'Data de entrega' in cell.get_text():
                                # A data deve estar na próxima célula
                                if i + 1 < len(cells):
                                    date_text = cells[i + 1].get_text(strip=True)
                                    logger.debug(f"Data encontrada na linha: {date_text}")

                                    parsed_date = self._parse_due_date(date_text)
                                    if parsed_date:
                                        logger.info(f"Data de entrega extraída da linha: {parsed_date}")
                                        return parsed_date

            # ESTRATÉGIA ALTERNATIVA 2: Buscar por seção "Status de envio" (método anterior como fallback)
            status_section = soup.find('h3', string=lambda text: text and 'Status de envio' in text)
            if status_section:
                status_container = status_section.find_next('div')
                if status_container:
                    status_text = status_container.get_text()
                    logger.debug(f"Status de envio encontrado: {status_text}")

                    parsed_date = self._parse_due_date(status_text)
                    if parsed_date:
                        logger.info(f"Data extraída do status de envio: {parsed_date}")
                        return parsed_date

            # ESTRATÉGIA ALTERNATIVA 3: Buscar por qualquer texto que contenha padrões de data
            submission_info = soup.find(string=re.compile(r'aceitará envios|prazo|até|vencimento|entrega', re.IGNORECASE))
            if submission_info:
                parent = submission_info.parent
                if parent:
                    text = parent.get_text()
                    logger.debug(f"Informação de envio encontrada: {text}")

                    parsed_date = self._parse_due_date(text)
                    if parsed_date:
                        logger.info(f"Data extraída de informação de envio: {parsed_date}")
                        return parsed_date

            # ESTRATÉGIA ALTERNATIVA 4: Buscar em todas as tabelas
            tables = soup.find_all('table')
            for table in tables:
                table_text = table.get_text()
                if any(keyword in table_text.lower() for keyword in ['prazo', 'vencimento', 'até', 'entrega', 'data']):
                    logger.debug(f"Tabela com informação de data encontrada")
                    parsed_date = self._parse_due_date(table_text)
                    if parsed_date:
                        logger.info(f"Data extraída de tabela: {parsed_date}")
                        return parsed_date

            logger.debug(f"Nenhuma data de vencimento encontrada para: {activity_url}")
            return None

        except requests.RequestException as e:
            logger.error(f"Erro ao acessar atividade {activity_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao extrair data da atividade {activity_url}: {e}")
            return None

    def _extract_assignments_from_main_page(self, soup, course_url: str) -> List[Dict]:
        """
        Fallback: Extrai atividades da página principal (método anterior)
        """
        assignments = []

        # Buscar por qualquer link que contenha módulos do Moodle
        all_mod_links = soup.select('a[href*="mod/"]')
        logger.info(f"Encontrados {len(all_mod_links)} links de módulos para análise detalhada")

        for link in all_mod_links:
            try:
                href = link.get('href')
                if not href:
                    continue

                # Tentar extrair título
                title = link.get_text(strip=True)
                if not title:
                    title = link.get('title') or link.get('aria-label')

                if title and len(title.strip()) > 2:
                    title = title.strip()

                    # Filtrar atividades que devem ser ignoradas
                    title_lower = title.lower().strip()
                    if ('envio de tarefa fora do prazo' in title_lower or
                        'envio de tarefa fora de prazo' in title_lower or
                        'fora do prazo' in title_lower):
                        logger.debug(f"Ignorando atividade (página principal): {title}")
                        continue

                    # Converter link relativo para absoluto
                    if not href.startswith('http'):
                        href = urljoin(course_url, href)

                    # Determinar tipo
                    activity_type = 'assignment'
                    if 'mod/quiz' in href:
                        activity_type = 'quiz'
                    elif 'mod/forum' in href:
                        activity_type = 'forum'
                    elif 'mod/assign' in href:
                        activity_type = 'assignment'
                    elif 'mod/folder' in href:
                        activity_type = 'folder'
                    elif 'mod/page' in href:
                        activity_type = 'page'

                    assignment_data = {
                        'title': title,
                        'url': href,
                        'due_date': None,
                        'type': activity_type,
                        'course_url': course_url
                    }

                    # Extrair data de vencimento acessando a página da atividade
                    due_date = self._extract_due_date_from_activity(href)
                    if due_date:
                        assignment_data['due_date'] = due_date

                    # Evitar duplicatas
                    if not any(a['title'] == title for a in assignments):
                        assignments.append(assignment_data)
                        logger.info(f"Atividade encontrada (página principal): {title} ({activity_type}) - Prazo: {due_date or 'Não definido'}")

            except Exception as e:
                logger.debug(f"Erro ao processar link na busca principal: {str(e)}")
                continue

        return assignments

    def _parse_due_date(self, date_text: str) -> Optional[date]:
        """
        Converte texto de data em objeto date

        Args:
            date_text (str): Texto contendo a data

        Returns:
            Optional[date]: Data convertida ou None se não conseguir converter
        """
        if not date_text:
            return None

        # Limpar o texto
        date_text = date_text.strip()

        # Padrões de data comuns em português (incluindo os novos formatos)
        date_patterns = [
            r'(\w+),\s*(\d{1,2})\s+(\w+)\s+(\d{4}),\s*(\d{1,2}):(\d{2})',  # domingo, 9 Nov 2025, 23:59
            r'(\d{1,2})\s+(\w+)\s+(\d{4}),\s*(\d{1,2}):(\d{2})',           # 9 Nov 2025, 23:59
            r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',                      # 9 de novembro de 2025
            r'(\d{1,2})\s+(\w+)\s+(\d{4})',                                # 9 novembro 2025
            r'(\d{1,2})/(\d{1,2})/(\d{4})',                                # dd/mm/yyyy
            r'(\d{1,2})-(\d{1,2})-(\d{4})',                                # dd-mm-yyyy
            r'(\d{4})-(\d{1,2})-(\d{1,2})',                                # yyyy-mm-dd
        ]

        # Mapeamento de meses em português (completo e abreviado)
        months = {
            'janeiro': 1, 'jan': 1,
            'fevereiro': 2, 'fev': 2,
            'março': 3, 'mar': 3,
            'abril': 4, 'abr': 4,
            'maio': 5, 'mai': 5,
            'junho': 6, 'jun': 6,
            'julho': 7, 'jul': 7,
            'agosto': 8, 'ago': 8,
            'setembro': 9, 'set': 9,
            'outubro': 10, 'out': 10,
            'novembro': 11, 'nov': 11,
            'dezembro': 12, 'dez': 12,
        }

        for pattern in date_patterns:
            matches = re.findall(pattern, date_text, re.IGNORECASE)
            for match in matches:
                try:
                    if len(match) == 6:  # sábado, 13 Set 2025, 08:00
                        _, day, month_name, year, hour, minute = match
                        month = months.get(month_name.lower())
                        if month:
                            return date(int(year), month, int(day))
                    elif len(match) == 5:  # 13 Set 2025, 08:00
                        day, month_name, year, hour, minute = match
                        month = months.get(month_name.lower())
                        if month:
                            return date(int(year), month, int(day))
                    elif len(match) == 3:
                        if pattern == r'(\d{4})-(\d{1,2})-(\d{1,2})':  # yyyy-mm-dd
                            year, month, day = match
                            return date(int(year), int(month), int(day))
                        elif 'de' in pattern:  # dd de mês de yyyy
                            day, month_name, year = match
                            month = months.get(month_name.lower())
                            if month:
                                return date(int(year), month, int(day))
                        elif month_name := match[1]:  # dd mês yyyy
                            day, month_name, year = match
                            month = months.get(month_name.lower())
                            if month:
                                return date(int(year), month, int(day))
                        else:  # dd/mm/yyyy ou dd-mm-yyyy
                            day, month, year = match
                            return date(int(year), int(month), int(day))
                except (ValueError, IndexError, TypeError) as e:
                    logger.debug(f"Erro ao converter data {match}: {e}")
                    continue

        # Tentar buscar por palavras-chave de prazo
        if any(keyword in date_text.lower() for keyword in ['até', 'prazo', 'entrega', 'vencimento', 'aceitará envios']):
            # Extrair apenas números que podem ser data
            numbers = re.findall(r'\d+', date_text)
            if len(numbers) >= 3:
                try:
                    # Assumir formato dd/mm/yyyy
                    day, month, year = numbers[:3]
                    if len(year) == 2:
                        year = '20' + year
                    return date(int(year), int(month), int(day))
                except ValueError:
                    pass

        logger.debug(f"Não foi possível converter a data: {date_text}")
        return None

    def scrape_all_data(self) -> Dict:
        """
        Executa scraping completo de disciplinas e atividades

        Returns:
            Dict: Dados completos extraídos
        """
        result = {
            'success': False,
            'courses': [],
            'assignments_count': 0,
            'error': None
        }

        try:
            # Fazer login
            if not self.login():
                result['error'] = 'Falha no login'
                return result

            # Buscar disciplinas
            courses = self.get_courses()

            # Para cada disciplina, buscar atividades
            for course in courses:
                if course.get('link'):
                    assignments = self.get_assignments(course['link'])
                    course['assignments'] = assignments
                    result['assignments_count'] += len(assignments)
                else:
                    course['assignments'] = []

            result['courses'] = courses
            result['success'] = True

            logger.info(f"Scraping concluído: {len(courses)} disciplinas, {result['assignments_count']} atividades")

        except Exception as e:
            logger.error(f"Erro no scraping completo: {str(e)}")
            result['error'] = str(e)

        return result

    def close(self):
        """
        Fecha a sessão
        """
        self.session.close()


class CredentialsManager:
    """
    Gerenciador de credenciais com criptografia
    """

    @staticmethod
    def encrypt_password(password: str) -> str:
        """
        Criptografa a senha
        """
        import base64
        from django.conf import settings

        # Gerar uma chave Fernet válida a partir da SECRET_KEY
        key_source = settings.SECRET_KEY.encode()[:32]  # Usar 32 bytes
        key_source = key_source.ljust(32, b'0')  # Preencher com zeros se necessário
        key = base64.urlsafe_b64encode(key_source)

        fernet = Fernet(key)
        return fernet.encrypt(password.encode()).decode()

    @staticmethod
    def decrypt_password(encrypted_password: str) -> str:
        """
        Descriptografa a senha
        """
        import base64
        from django.conf import settings

        # Gerar a mesma chave usada na criptografia
        key_source = settings.SECRET_KEY.encode()[:32]
        key_source = key_source.ljust(32, b'0')
        key = base64.urlsafe_b64encode(key_source)

        fernet = Fernet(key)
        return fernet.decrypt(encrypted_password.encode()).decode()
