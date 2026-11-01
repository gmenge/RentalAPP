# Changelog

Mudanças do LocaFácil, sistema desktop de gestão de aluguéis de equipamentos.

## Atualização de 01/11/2026

### Importante

- **Os dados agora ficam salvos no `.exe`.** Antes, tudo o que era cadastrado no executável se perdia ao fechar o programa. Os dados agora ficam em `%APPDATA%\LocaFacil`, junto com um backup automático. O que foi cadastrado nas versões antigas do executável não pode ser recuperado.

### Novidades

**Equipamentos**

- Importação de listas a partir de arquivos `.xlsx`, `.xlsm`, `.xls`, `.ods`, `.csv`, `.tsv`, `.txt`, `.xml`, `.json` e `.docx`, com prévia antes de salvar. As linhas com erro aparecem com o motivo e são ignoradas.
- Colunas reconhecidas pelo título, em qualquer ordem. Sem títulos, a ordem é Nome, Marca, Categoria, Diária, Quantidade, Patrimônio.
- Botão **Baixar Modelo** com uma planilha pronta para preencher.
- Campo **Número de Patrimônio**, opcional e sem repetição, no cadastro, na tabela, na pesquisa e na importação.
- Campo de quantidade no cadastro e edição de equipamentos já cadastrados, pelo botão **Editar** ou com duplo clique na linha.
- Ordenação da tabela ao clicar no título de qualquer coluna.

**Contratos**

- Um contrato agora pode ter vários equipamentos, com total calculado na hora.
- Busca de equipamento ao digitar, com lista que abre ao clicar no campo e rola com a roda do mouse.
- Estoque por período: um aluguel só reduz a disponibilidade nas datas dele, e reservas acima do estoque são bloqueadas.
- Edição e exclusão de contratos finalizados no histórico.

### Alterações

- Novo visual minimalista em tons de cinza, com um único botão de destaque por tela. A cor fica reservada para atrasos e erros.
- Aluguéis atrasados continuam ocupando o estoque até a devolução ser registrada.
- Um equipamento em contrato aberto não pode mais ser excluído.

### Correções

- O programa parava de abrir depois do primeiro aluguel em aberto.
- O histórico de contratos concluídos ficava sempre vazio.
- As colunas da tabela do Dashboard não se alinhavam com os títulos.

### Segurança

- O executável passa a usar o `pillow` 13.0.0, que corrige vulnerabilidades conhecidas das versões anteriores.

### Para quem compila o projeto

- Novas dependências: `tkcalendar`, `openpyxl`, `xlrd`, `odfpy`, `python-docx` e `pillow`. Instale com `pip install -r requirements.txt`.
- Gere o executável com `pyinstaller --noconfirm main.spec`.
- Bancos de dados existentes são atualizados automaticamente ao abrir o programa.
- Arquivos `.doc` antigos não são lidos: salve-os como `.docx` antes de importar.
