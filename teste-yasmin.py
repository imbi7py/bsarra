import sqlite3

conn = sqlite3.connect('sarra.db') # Carregando banco de dados
cursor = conn.cursor()
estado='MG'
cursor.execute('''
SELECT *
FROM cultura, configuracaoRegional, grupo, estado, estacao, municipio
WHERE cultura.id = configuracaoRegional.culturaID
AND configuracaoRegional.id = grupo.culturaRegiao AND municipio.codigo = estacao.municipio AND municipio.estado = estado.sigla AND estado.sigla = "%s"''' % (estado))

var = cursor.fetchall()

i=0
while i<len(var):
    print var[i]
    i=i+1