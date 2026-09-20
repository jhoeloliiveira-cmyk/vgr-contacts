# -*- coding: utf-8 -*-
"""Gera o contrato enxuto em .docx e .html a partir de uma fonte única.
Marcador de lacuna: {{n}} -> linha de preenchimento com n caracteres de largura."""
import re, html as H

# ---------------------------------------------------------------- conteúdo
# ("h", titulo) | ("p", texto justificado) | ("c", campo, alinhado à esquerda)
# ("nota", texto em itálico) | ("esp",) espaçador
BLOCOS = [
    ("h", "1. Partes"),
    ("p", "**CONTRATADO:** JARDEL EMERSON DA SILVA LINS, psicólogo, inscrito no CRP sob o nº 02/32710, "
          "CPF nº {{16}}, com consultório na Rua Vicente Barbosa, nº 117, Bairro São Pedro, Belo Jardim/PE."),
    ("c", "**CONTRATANTE (paciente):**"),
    ("c", "Nome completo: {{72}}"),
    ("c", "Data de nascimento: {{14}}   CPF: {{20}}   RG: {{20}}"),
    ("c", "Endereço: {{60}} nº {{8}}"),
    ("c", "Bairro: {{26}}   Cidade/UF: {{26}}   CEP: {{14}}"),
    ("c", "Telefone/WhatsApp: {{24}}   E-mail: {{34}}"),
    ("c", "Contato de emergência (nome e telefone): {{50}}"),
    ("nota", "Responsável legal — preencher apenas se o paciente for menor de 18 anos ou necessitar de representação:"),
    ("c", "Nome: {{46}}   Vínculo: {{26}}"),
    ("c", "CPF: {{22}}   Telefone: {{24}}"),
    ("p", "As partes acima contratam os serviços descritos a seguir, nos termos do Código de Ética Profissional "
          "do Psicólogo (Resolução CFP nº 010/2005) e demais resoluções do CFP, do Código Civil, do Código de "
          "Defesa do Consumidor e da Lei Geral de Proteção de Dados (Lei nº 13.709/2018)."),

    ("h", "2. Objeto"),
    ("p", "2.1. Atendimento psicológico na modalidade ( ) psicoterapia individual  ( ) psicoterapia de casal  "
          "( ) psicoterapia infantil/adolescente  ( ) avaliação psicológica  ( ) outro: {{20}}, prestado "
          "pessoalmente pelo CONTRATADO, na abordagem {{24}}."),
    ("p", "2.2. O serviço é obrigação de meio, e não de resultado: o CONTRATADO empregará sua melhor técnica e "
          "diligência, sem garantir resultado terapêutico específico, cura ou prazo determinado. O atendimento "
          "psicológico não substitui acompanhamento médico ou psiquiátrico."),

    ("h", "3. Sessões"),
    ("p", "3.1. Modalidade: ( ) presencial, no consultório  ( ) on-line, pela plataforma {{20}} "
          "(Resolução CFP nº 11/2018)  ( ) híbrida."),
    ("p", "3.2. Duração de {{7}} minutos, contados do horário marcado, ainda que o CONTRATANTE chegue atrasado."),
    ("p", "3.3. Frequência de {{5}} sessão(ões) por ( ) semana  ( ) quinzena  ( ) mês, em dia e horário fixos: "
          "{{18}}, às {{9}}, reservados com exclusividade ao CONTRATANTE."),

    ("h", "4. Honorários"),
    ("p", "4.1. Valor de R$ {{12}} ({{34}}) por sessão, pago ( ) ao final de cada sessão  ( ) até o dia {{5}} "
          "de cada mês, por ( ) PIX — chave {{20}}  ( ) transferência  ( ) cartão  ( ) dinheiro."),
    ("p", "4.2. Em caso de atraso, incidirá multa de {{5}}% e juros de {{5}}% ao mês. Persistindo a inadimplência, "
          "os atendimentos poderão ser suspensos mediante aviso prévio de {{5}} dias, com o devido encaminhamento "
          "do CONTRATANTE."),
    ("p", "4.3. Os honorários serão reajustados a cada 12 meses, com aviso de 30 dias de antecedência."),
    ("p", "4.4. Recibo (RPA) ou nota fiscal será fornecido quando solicitado. Relatórios, laudos, declarações, "
          "reuniões escolares, audiências e perícias são cobrados à parte, mediante acordo prévio."),

    ("h", "5. Faltas, atrasos e cancelamentos"),
    ("p", "5.1. Cancelamentos e remarcações devem ser comunicados com antecedência mínima de {{5}} horas."),
    ("p", "5.2. A falta não comunicada nesse prazo ( ) será cobrada integralmente  ( ) será cobrada em {{5}}%  "
          "( ) não será cobrada, uma vez que o horário permaneceu reservado."),
    ("p", "5.3. O atraso do CONTRATANTE não prorroga o término da sessão. Caso o CONTRATADO precise cancelar, a "
          "sessão será reposta sem custo adicional, em data conveniente a ambos."),

    ("h", "6. Sigilo profissional"),
    ("p", "6.1. O CONTRATADO mantém sigilo sobre tudo o que souber em razão do atendimento, inclusive após o "
          "término do contrato (arts. 9º a 13 do Código de Ética do Psicólogo e art. 154 do Código Penal)."),
    ("p", "6.2. O sigilo só é rompido, no mínimo necessário, em caso de: (a) risco atual de morte ou lesão grave "
          "ao CONTRATANTE ou a terceiros; (b) suspeita de violência contra criança, adolescente, pessoa idosa ou "
          "pessoa com deficiência; (c) ordem judicial; (d) autorização escrita do CONTRATANTE. Sempre que "
          "possível, o CONTRATANTE será avisado previamente."),
    ("p", "6.3. No atendimento de crianças e adolescentes, os responsáveis recebem orientações gerais sobre o "
          "processo terapêutico, sem detalhamento do conteúdo das sessões, ressalvadas as hipóteses do item 6.2."),

    ("h", "7. Registros e proteção de dados (LGPD)"),
    ("p", "7.1. O prontuário psicológico é guardado em local seguro, de acesso restrito, por no mínimo 5 anos "
          "(Resolução CFP nº 001/2009). Os dados do CONTRATANTE são usados apenas para o atendimento e para o "
          "cumprimento de obrigações legais."),
    ("p", "7.2. É vedada a gravação das sessões, em áudio ou vídeo, por qualquer das partes, salvo autorização "
          "expressa e por escrito de ambas."),

    ("h", "8. Compromissos das partes"),
    ("p", "8.1. O CONTRATADO compromete-se a cumprir o Código de Ética e as resoluções do CFP, manter seu "
          "registro ativo no CRP, respeitar os horários, esclarecer dúvidas sobre o processo terapêutico e "
          "encaminhar o CONTRATANTE a outro profissional ou serviço quando a demanda fugir de sua área de atuação."),
    ("p", "8.2. O CONTRATANTE compromete-se a comparecer nos horários combinados, pagar em dia, prestar "
          "informações verdadeiras (inclusive sobre medicamentos e outros tratamentos em curso), avisar faltas, "
          "manter seus contatos atualizados e não comparecer sob efeito de álcool ou outras substâncias — "
          "hipótese em que a sessão poderá ser encerrada e cobrada."),
    ("p", "8.3. No atendimento on-line, cabe ao CONTRATANTE dispor de conexão, equipamento e ambiente reservado. "
          "Havendo queda de conexão por mais de {{5}} minutos, a sessão será remarcada."),
    ("c", "Endereço de onde o CONTRATANTE participará das sessões on-line: {{42}}"),

    ("h", "9. Vigência e encerramento"),
    ("p", "9.1. Vigência por prazo ( ) indeterminado, a partir de {{14}}  ( ) determinado, de {{14}} a {{14}}."),
    ("p", "9.2. Qualquer das partes pode encerrar o contrato a qualquer tempo, com aviso de {{5}} dias e sem "
          "multa, pagas as sessões já realizadas. Recomenda-se {{5}} sessão(ões) de encerramento."),
    ("p", "9.3. O CONTRATADO não abandonará o CONTRATANTE: havendo interrupção por sua iniciativa, informará os "
          "motivos e fará o encaminhamento a outro profissional ou serviço."),

    ("h", "10. Disposições finais"),
    ("p", "10.1. O CONTRATANTE declara ter sido informado, em linguagem clara, sobre os objetivos, o método, a "
          "duração estimada, os limites do sigilo e os valores do atendimento, e que sua participação é "
          "voluntária, podendo interrompê-la a qualquer momento."),
    ("p", "10.2. Alterações deste contrato só valem por escrito, assinadas por ambas as partes."),
    ("p", "10.3. Fica eleito o foro da comarca de Belo Jardim/PE para dirimir dúvidas oriundas deste contrato."),

    ("p", "E, por estarem de acordo, as partes assinam este instrumento em 2 (duas) vias de igual teor."),
    ("c", "{{26}}, {{5}} de {{16}} de {{9}}."),
]

FIRMAS = [
    ("JARDEL EMERSON DA SILVA LINS", "Psicólogo — CRP 02/32710  ·  CONTRATADO", None),
    (None, "CONTRATANTE (paciente)", "Nome: {{26}}   CPF: {{16}}"),
    (None, "RESPONSÁVEL LEGAL (quando aplicável)", "Nome: {{26}}   CPF: {{16}}"),
]
TESTEMUNHAS = ["1) {{40}}   CPF: {{18}}", "2) {{40}}   CPF: {{18}}"]

CAB_TEL = "Telefone: {{18}}"
CAB_MAIL = "E-mail: {{28}}"

# ---------------------------------------------------------------- utilidades
LACUNA = re.compile(r"\{\{(\d+)\}\}")
NEGRITO = re.compile(r"\*\*(.+?)\*\*")

NBSP = '\u00a0'

def nao_quebrar(texto):
    """Impede que as caixas de seleção '( )' quebrem entre linhas."""
    return texto.replace('( )', '(' + NBSP + ')')

def partes(texto):
    """Divide o texto em (tipo, valor): ('t', txt) | ('b', txt negrito) | ('l', largura)."""
    saida = []
    for pedaco in NEGRITO.split(texto):
        pass
    texto = nao_quebrar(texto)
    pos, bold = 0, False
    for m in NEGRITO.finditer(texto):
        if m.start() > pos:
            saida.append(('t', texto[pos:m.start()]))
        saida.append(('b', m.group(1)))
        pos = m.end()
    if pos < len(texto):
        saida.append(('t', texto[pos:]))
    final = []
    for tipo, val in saida:
        if tipo == 'b':
            final.append(('b', val)); continue
        ini = 0
        for m in LACUNA.finditer(val):
            if m.start() > ini:
                final.append(('t', val[ini:m.start()]))
            final.append(('l', int(m.group(1))))
            ini = m.end()
        if ini < len(val):
            final.append(('t', val[ini:]))
    return final

# ---------------------------------------------------------------- DOCX
def gerar_docx(caminho):
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    VERDE = RGBColor(0x2F, 0x5D, 0x50)
    doc = Document()
    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    s.top_margin, s.bottom_margin = Cm(1.5), Cm(1.3)
    s.left_margin, s.right_margin = Cm(1.8), Cm(1.8)

    normal = doc.styles['Normal']
    normal.font.name = 'Calibri'
    normal.font.size = Pt(10)
    normal._element.rPr.rFonts.set(qn('w:eastAsia'), 'Calibri')
    pf = normal.paragraph_format
    pf.space_after, pf.space_before, pf.line_spacing = Pt(3), Pt(0), 1.02

    ORDEM_POS_PBDR = (
        'w:shd','w:tabs','w:suppressAutoHyphens','w:kinsoku','w:wordWrap','w:overflowPunct',
        'w:topLinePunct','w:autoSpaceDE','w:autoSpaceDN','w:bidi','w:adjustRightInd','w:snapToGrid',
        'w:spacing','w:ind','w:contextualSpacing','w:mirrorIndents','w:suppressOverlap','w:jc',
        'w:textDirection','w:textAlignment','w:textboxTightWrap','w:outlineLvl','w:divId','w:cnfStyle',
        'w:rPr','w:sectPr','w:pPrChange')

    def borda(par, cor='B8B2A4', sz=6):
        pPr = par._p.get_or_add_pPr()
        pbdr = OxmlElement('w:pBdr'); b = OxmlElement('w:bottom')
        b.set(qn('w:val'), 'single'); b.set(qn('w:sz'), str(sz))
        b.set(qn('w:space'), '2'); b.set(qn('w:color'), cor)
        pbdr.append(b); pPr.insert_element_before(pbdr, *ORDEM_POS_PBDR)

    def escrever(texto, align, before=0, after=4, size=None, bold=False, italic=False, cor=None):
        par = doc.add_paragraph()
        par.paragraph_format.alignment = align
        par.paragraph_format.space_before = Pt(before)
        par.paragraph_format.space_after = Pt(after)
        for tipo, val in partes(texto):
            r = par.add_run('_' * val if tipo == 'l' else val)
            r.bold = bold or tipo == 'b'
            r.italic = italic
            if size: r.font.size = Pt(size)
            if cor: r.font.color.rgb = cor
        return par

    J, E, C = WD_ALIGN_PARAGRAPH.JUSTIFY, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER

    escrever('JARDEL EMERSON DA SILVA LINS', C, after=0, size=13, bold=True)
    escrever('Psicólogo  ·  CRP 02/32710', C, after=0, size=9.5)
    escrever('Rua Vicente Barbosa, nº 117 — São Pedro — Belo Jardim/PE', C, after=0, size=9)
    cab = escrever(CAB_TEL + '   ·   ' + CAB_MAIL, C, after=2, size=9)
    borda(cab, '444444', 8)
    escrever('CONTRATO DE PRESTAÇÃO DE SERVIÇOS PSICOLÓGICOS', C, before=9, after=1, size=12.5, bold=True)
    escrever('Modelo — preencher as lacunas antes da assinatura', C, after=3, size=9, italic=True)

    from docx.oxml.ns import qn as _qn
    from docx.shared import Emu
    LARGURA_UTIL = 10092         # 17,8 cm em DXA
    DXA_POR_CHAR = 94            # largura média de caractere em Calibri 10pt

    POS_TBL_BORDERS = ('w:shd', 'w:tblLayout', 'w:tblCellMar', 'w:tblLook',
                       'w:tblCaption', 'w:tblDescription', 'w:tblPrChange')
    POS_TBL_LAYOUT = ('w:tblCellMar', 'w:tblLook', 'w:tblCaption', 'w:tblDescription', 'w:tblPrChange')
    POS_TBL_CELLMAR = ('w:tblLook', 'w:tblCaption', 'w:tblDescription', 'w:tblPrChange')
    POS_TC_BORDERS = ('w:shd', 'w:noWrap', 'w:tcMar', 'w:textDirection', 'w:tcFitText',
                      'w:vAlign', 'w:hideMark', 'w:tcPrChange')
    POS_TC_VALIGN = ('w:hideMark', 'w:tcPrChange')

    def _prop(el, tag, **attrs):
        e = OxmlElement(tag)
        for k, v in attrs.items():
            e.set(_qn('w:' + k), str(v))
        el.append(e)
        return e

    def campo_tabela(texto):
        itens = partes(texto)
        if not any(t == 'l' for t, _ in itens):
            return escrever(texto, E, after=4)
        rotulos = sum(len(v) * DXA_POR_CHAR for t, v in itens if t != 'l')
        peso = sum(v for t, v in itens if t == 'l')
        sobra = max(LARGURA_UTIL - rotulos, 800)
        larguras = []
        for t, v in itens:
            larguras.append(max(int(sobra * v / peso), 400) if t == 'l' else len(v) * DXA_POR_CHAR)
        excesso = sum(larguras) - LARGURA_UTIL
        if excesso > 0:                      # reduz as lacunas proporcionalmente
            lac = [i for i, (t, _) in enumerate(itens) if t == 'l']
            total_lac = sum(larguras[i] for i in lac)
            for i in lac:
                larguras[i] -= int(excesso * larguras[i] / total_lac)

        tab = doc.add_table(rows=1, cols=len(itens))
        tab.autofit = False
        tblPr = tab._tbl.tblPr
        bordas = OxmlElement('w:tblBorders')
        for lado in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            _prop(bordas, 'w:' + lado, val='none', sz=0, space=0, color='auto')
        tblPr.insert_element_before(bordas, *POS_TBL_BORDERS)
        # tab.autofit = False já emite <w:tblLayout w:type="fixed"/>
        margens = OxmlElement('w:tblCellMar')
        for lado in ('top', 'left', 'bottom', 'right'):
            _prop(margens, 'w:' + lado, w=0, type='dxa')
        tblPr.insert_element_before(margens, *POS_TBL_CELLMAR)

        for idx, ((tipo_item, valor), larg) in enumerate(zip(itens, larguras)):
            cel = tab.cell(0, idx)
            cel.width = Emu(int(larg * 635))          # 1 DXA = 635 EMU
            tab.columns[idx].width = Emu(int(larg * 635))
            par = cel.paragraphs[0]
            par.paragraph_format.space_after = Pt(0)
            par.paragraph_format.space_before = Pt(0)
            tcPr = cel._tc.get_or_add_tcPr()
            if tipo_item == 'l':
                bord = OxmlElement('w:tcBorders')
                _prop(bord, 'w:bottom', val='single', sz=6, space=0, color='8D8678')
                tcPr.insert_element_before(bord, *POS_TC_BORDERS)
            else:
                r = par.add_run(valor)
                r.bold = (tipo_item == 'b')
            valign = OxmlElement('w:vAlign'); valign.set(_qn('w:val'), 'bottom')
            tcPr.insert_element_before(valign, *POS_TC_VALIGN)
        espaco = doc.add_paragraph()
        espaco.paragraph_format.space_before = Pt(0)
        espaco.paragraph_format.space_after = Pt(0)
        espaco.add_run('').font.size = Pt(5)
        return tab

    for bloco in BLOCOS:
        tipo = bloco[0]
        if tipo == 'h':
            borda(escrever(bloco[1].upper(), E, before=6, after=3, bold=True, cor=VERDE))
        elif tipo == 'p':
            escrever(bloco[1], J)
        elif tipo == 'c':
            campo_tabela(bloco[1])
        elif tipo == 'nota':
            escrever(bloco[1], E, before=2, after=4, size=9, italic=True)
        elif tipo == 'esp':
            escrever('', E, after=2)

    for nome, cargo, dados in FIRMAS:
        escrever('_' * 44, C, before=11, after=0)
        if nome: escrever(nome, C, after=0, bold=True)
        escrever(cargo, C, after=0, size=9)
        if dados: escrever(dados, C, after=0, size=9)

    escrever('Testemunhas:', E, before=9, after=3, size=9.5, bold=True)
    for t in TESTEMUNHAS:
        escrever(t, E, after=5, size=9.5)

    zoom = doc.settings.element.find(qn('w:zoom'))
    if zoom is not None and zoom.get(qn('w:percent')) is None:
        zoom.set(qn('w:percent'), '100')

    doc.save(caminho)

# ---------------------------------------------------------------- HTML
CSS = """
  :root{ --ink:#161512; --soft:#4a463f; --rule:#b8b2a4; --accent:#2f5d50; --blank:#8d8678; }
  @page{ size:A4; margin:15mm 18mm 13mm; }
  *{ box-sizing:border-box; }
  body{ margin:0; background:#e9e6df; color:var(--ink);
    font-family:Calibri,Carlito,"Liberation Sans",Arial,sans-serif; font-size:10pt; line-height:1.24; }
  .folha{ max-width:210mm; margin:0 auto; background:#fff; padding:15mm 18mm 13mm;
    box-shadow:0 1px 3px rgba(0,0,0,.14); }
  .cab{ text-align:center; border-bottom:1px solid #444; padding-bottom:3px; }
  .cab .nome{ font-size:13pt; font-weight:700; }
  .cab .crp{ font-size:9.5pt; }
  .cab .end{ font-size:9pt; color:var(--soft); }
  h1{ font-size:12.5pt; text-align:center; text-transform:uppercase; letter-spacing:.02em; margin:9px 0 1px; }
  .sub{ text-align:center; font-size:9pt; font-style:italic; color:var(--soft); margin:0 0 5px; }
  h2{ font-size:10pt; color:var(--accent); text-transform:uppercase; letter-spacing:.02em;
    margin:7px 0 3px; padding-bottom:2px; border-bottom:1px solid var(--rule);
    page-break-after:avoid; break-after:avoid; }
  p{ margin:0 0 3px; text-align:justify; }
  p.campo{ text-align:left; margin-bottom:5px; display:flex; align-items:baseline; }
  p.campo .t{ white-space:pre; flex:none; }
  p.campo .l{ flex:1 1 0; min-width:12mm; }
  p.nota{ text-align:left; font-size:9pt; font-style:italic; color:var(--soft); margin:3px 0 5px; }
  .l{ display:inline-block; border-bottom:1px solid var(--blank); height:1em; vertical-align:-1px; }
  .firma{ text-align:center; margin-top:11px; page-break-inside:avoid; break-inside:avoid; }
  .firma .traco{ border-top:1px solid var(--ink); width:78mm; margin:0 auto 3px; }
  .firma .nome{ font-weight:700; }
  .firma .cargo{ font-size:9pt; color:var(--soft); }
  .firma .dados{ font-size:9pt; }
  .test{ margin-top:10px; font-size:9.5pt; }
  .test p{ margin:0 0 6px; text-align:left; }
  .fim{ page-break-inside:avoid; break-inside:avoid; }
  @media print{ body{ background:#fff; } .folha{ box-shadow:none; padding:0; max-width:none; } }
  @media (max-width:640px){ .folha{ padding:16px; } body{ font-size:12px; line-height:1.45; }
    .l{ max-width:100%; } }
"""

def html_texto(texto, flex=False):
    saida = []
    for tipo, val in partes(texto):
        if tipo == 'l':
            if flex:
                saida.append('<span class="l" style="flex-grow:%d"></span>' % val)
            else:
                saida.append('<span class="l" style="width:%dch"></span>' % val)
        elif tipo == 'b':
            saida.append('<b class="t">%s</b>' % H.escape(val) if flex else '<b>%s</b>' % H.escape(val))
        else:
            if flex:
                saida.append('<span class="t">%s</span>' % H.escape(val))
            else:
                saida.append(H.escape(val).replace('  ', '&nbsp;&nbsp;'))
    return ''.join(saida)

def gerar_html(caminho):
    corpo = []
    from docx.oxml.ns import qn as _qn
    from docx.shared import Emu
    LARGURA_UTIL = 10092         # 17,8 cm em DXA
    DXA_POR_CHAR = 94            # largura média de caractere em Calibri 10pt

    POS_TBL_BORDERS = ('w:shd', 'w:tblLayout', 'w:tblCellMar', 'w:tblLook',
                       'w:tblCaption', 'w:tblDescription', 'w:tblPrChange')
    POS_TBL_LAYOUT = ('w:tblCellMar', 'w:tblLook', 'w:tblCaption', 'w:tblDescription', 'w:tblPrChange')
    POS_TBL_CELLMAR = ('w:tblLook', 'w:tblCaption', 'w:tblDescription', 'w:tblPrChange')
    POS_TC_BORDERS = ('w:shd', 'w:noWrap', 'w:tcMar', 'w:textDirection', 'w:tcFitText',
                      'w:vAlign', 'w:hideMark', 'w:tcPrChange')
    POS_TC_VALIGN = ('w:hideMark', 'w:tcPrChange')

    def _prop(el, tag, **attrs):
        e = OxmlElement(tag)
        for k, v in attrs.items():
            e.set(_qn('w:' + k), str(v))
        el.append(e)
        return e

    def campo_tabela(texto):
        itens = partes(texto)
        if not any(t == 'l' for t, _ in itens):
            return escrever(texto, E, after=4)
        rotulos = sum(len(v) * DXA_POR_CHAR for t, v in itens if t != 'l')
        peso = sum(v for t, v in itens if t == 'l')
        sobra = max(LARGURA_UTIL - rotulos, 800)
        larguras = []
        for t, v in itens:
            larguras.append(max(int(sobra * v / peso), 400) if t == 'l' else len(v) * DXA_POR_CHAR)
        excesso = sum(larguras) - LARGURA_UTIL
        if excesso > 0:                      # reduz as lacunas proporcionalmente
            lac = [i for i, (t, _) in enumerate(itens) if t == 'l']
            total_lac = sum(larguras[i] for i in lac)
            for i in lac:
                larguras[i] -= int(excesso * larguras[i] / total_lac)

        tab = doc.add_table(rows=1, cols=len(itens))
        tab.autofit = False
        tblPr = tab._tbl.tblPr
        bordas = OxmlElement('w:tblBorders')
        for lado in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            _prop(bordas, 'w:' + lado, val='none', sz=0, space=0, color='auto')
        tblPr.insert_element_before(bordas, *POS_TBL_BORDERS)
        # tab.autofit = False já emite <w:tblLayout w:type="fixed"/>
        margens = OxmlElement('w:tblCellMar')
        for lado in ('top', 'left', 'bottom', 'right'):
            _prop(margens, 'w:' + lado, w=0, type='dxa')
        tblPr.insert_element_before(margens, *POS_TBL_CELLMAR)

        for idx, ((tipo_item, valor), larg) in enumerate(zip(itens, larguras)):
            cel = tab.cell(0, idx)
            cel.width = Emu(int(larg * 635))          # 1 DXA = 635 EMU
            tab.columns[idx].width = Emu(int(larg * 635))
            par = cel.paragraphs[0]
            par.paragraph_format.space_after = Pt(0)
            par.paragraph_format.space_before = Pt(0)
            tcPr = cel._tc.get_or_add_tcPr()
            if tipo_item == 'l':
                bord = OxmlElement('w:tcBorders')
                _prop(bord, 'w:bottom', val='single', sz=6, space=0, color='8D8678')
                tcPr.insert_element_before(bord, *POS_TC_BORDERS)
            else:
                r = par.add_run(valor)
                r.bold = (tipo_item == 'b')
            valign = OxmlElement('w:vAlign'); valign.set(_qn('w:val'), 'bottom')
            tcPr.insert_element_before(valign, *POS_TC_VALIGN)
        espaco = doc.add_paragraph()
        espaco.paragraph_format.space_before = Pt(0)
        espaco.paragraph_format.space_after = Pt(0)
        espaco.add_run('').font.size = Pt(5)
        return tab

    for bloco in BLOCOS:
        tipo = bloco[0]
        if tipo == 'h':
            corpo.append('  <h2>%s</h2>' % H.escape(bloco[1]))
        elif tipo == 'p':
            corpo.append('  <p>%s</p>' % html_texto(bloco[1]))
        elif tipo == 'c':
            corpo.append('  <p class="campo">%s</p>' % html_texto(bloco[1], flex=True))
        elif tipo == 'nota':
            corpo.append('  <p class="nota">%s</p>' % H.escape(bloco[1]))
        elif tipo == 'esp':
            corpo.append('  <p>&nbsp;</p>')

    firmas = []
    for nome, cargo, dados in FIRMAS:
        firmas.append('  <div class="firma"><div class="traco"></div>')
        if nome: firmas.append('    <div class="nome">%s</div>' % H.escape(nome))
        firmas.append('    <div class="cargo">%s</div>' % H.escape(cargo))
        if dados: firmas.append('    <div class="dados">%s</div>' % html_texto(dados))
        firmas.append('  </div>')

    test = ['  <div class="test">', '    <p><b>Testemunhas:</b></p>']
    for t in TESTEMUNHAS:
        test.append('    <p>%s</p>' % html_texto(t))
    test.append('  </div>')

    doc = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Contrato Psicológico Resumido</title>
<meta name="description" content="Versão enxuta do contrato de prestação de serviços psicológicos, com lacunas para preenchimento.">
<style>{CSS}</style>
</head>
<body>
<div class="folha">

  <div class="cab">
    <div class="nome">JARDEL EMERSON DA SILVA LINS</div>
    <div class="crp">Psicólogo &nbsp;·&nbsp; CRP 02/32710</div>
    <div class="end">Rua Vicente Barbosa, nº 117 — São Pedro — Belo Jardim/PE</div>
    <div class="end">{html_texto(CAB_TEL)} &nbsp;·&nbsp; {html_texto(CAB_MAIL)}</div>
  </div>

  <h1>Contrato de Prestação de Serviços Psicológicos</h1>
  <p class="sub">Modelo — preencher as lacunas antes da assinatura</p>

{chr(10).join(corpo)}

  <div class="fim">
{chr(10).join(firmas)}
{chr(10).join(test)}
  </div>

</div>
</body>
</html>
"""
    open(caminho, 'w', encoding='utf-8').write(doc)

if __name__ == '__main__':
    import sys
    destino = sys.argv[1] if len(sys.argv) > 1 else '.'
    gerar_docx(destino + '/contrato-psicologia-resumido.docx')
    gerar_html(destino + '/contrato-psicologia-resumido.html')
    print('gerados em', destino)
