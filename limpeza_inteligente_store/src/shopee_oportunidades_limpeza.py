#!/usr/bin/env python3
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MODULE_DIR=ROOT/'limpeza_inteligente_store'; ROOT_SRC=ROOT/'src'
os.environ.setdefault('SHOPEE_OPPORTUNITIES_CONFIG',str(MODULE_DIR/'config/shopee_oportunidades.json'))
os.environ.setdefault('SHOPEE_INTENT_RULES',str(MODULE_DIR/'config/shopee_intent_rules.json'))
os.environ.setdefault('SHOPEE_OUTPUT_DIR',str(MODULE_DIR/'data/shopee_oportunidades'))
if str(ROOT_SRC) not in sys.path: sys.path.insert(0,str(ROOT_SRC))
import shopee_oportunidades_v23 as v23

def regression_checks(rules_doc):
    cases=[
      ('Robô Aspirador Inteligente Recarregável','robo aspirador',True),('Filtro para Robô Aspirador','robo aspirador',False),
      ('Robô Aspirador com Mapeamento Lidar','robo aspirador mapeamento',True),('Aspirador Vertical 2 em 1 600W','aspirador vertical 2 em 1',True),
      ('Filtro HEPA para Aspirador Vertical','aspirador vertical',False),('Mini Aspirador Sem Fio Recarregável USB','mini aspirador sem fio',True),
      ('Mop Giratório com Balde Centrífuga','mop giratorio',True),('Refil Avulso Mop Microfibra','mop giratorio',False),
      ('Mop Spray com Reservatório','mop spray',True),('Rodo Limpa Vidros Spray Microfibra','rodo limpa vidros spray',True),
      ('Limpador a Vapor Elétrico 1500W','limpador vapor',True),('Detergente Limpador a Vapor 1L','limpador vapor',False),
      ('Extratora Elétrica Estofados Sofá 1400W','extratora estofados',True),('Shampoo para Extratora Estofados','extratora estofados',False),
      ('Lavadora Alta Pressão Portátil Sem Fio','lavadora alta pressao portatil',True),('Mangueira para Lavadora Alta Pressão','lavadora alta pressao portatil',False),
    ]
    failures=[]
    for title,kw,expected in cases:
        actual=bool(v23.evaluate_keyword(title,kw,rules_doc).get('accepted'))
        if actual!=expected: failures.append({'title':title,'keyword':kw,'expected':expected,'actual':actual})
    if failures: raise SystemExit('Falha nos testes semânticos Limpeza Inteligente: '+repr(failures))
    print(f'Testes semânticos Limpeza Inteligente: {len(cases)}/{len(cases)} OK')

def main():
    v23.run_regression_checks=regression_checks
    print('=== LIMPEZA INTELIGENTE — SHOPEE OPORTUNIDADES ===')
    ranking=v23.scan_v23(); v23.print_v23(ranking)
if __name__=='__main__': main()
