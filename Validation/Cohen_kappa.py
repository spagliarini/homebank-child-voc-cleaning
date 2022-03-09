#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: silviapagliarini
"""
import os
import sklearn
import sklearn.metrics as sklm
import numpy as np
import xlsxwriter
import xlrd
import pandas as pd

def qualitative_table(args):
    """
    Build an excel table to run the test.
    - list of vocalizations (from 1 to N - number of vocalizations)
    - start (in seconds)
    - end (in seconds)
    - lena labels
    - columns containing the other judges' labels
    """

    # Read judge list
    if args.judge == 'all':
        judge_list_table = pd.read_csv(args.data_dir + '/' + args.baby_id + '_judges_list.csv')
    elif args.judge == 'common':
        judge_list_table = pd.read_csv(args.data_dir + '/' + 'common_judges_list.csv')
    judges_list_code = judge_list_table["judge_code"]
    judges_list_name = judge_list_table["judge_name"]

    n_test_table = pd.read_csv(args.data_dir + '/' + args.baby_id + '_scrubbed_CHNrelabel_' + judges_list_name[1] + '_1.csv')
    n_test = len(n_test_table["startSeconds"])
    n_test_start = n_test_table["startSeconds"]
    n_test_end = n_test_table["endSeconds"]

    # lena labels
    lena = pd.read_csv(args.data_dir + '/' + args.baby_id + '_segments.csv')
    lena_labels = lena["segtype"]

    CHNSP_pos = np.where(lena_labels == 'CHNSP')[0]
    CHNNSP_pos = np.where(lena_labels == 'CHNNSP')[0]
    pos = np.append(CHNSP_pos, CHNNSP_pos)
    pos = sorted(pos)

    # Creating content and common data
    content = ["test", "startsec", "endsec", "lena"]
    prominence = []
    for i in range(0, len(judges_list_name)):
        content.append(judges_list_name[i])
        human_table = pd.read_csv(args.data_dir + '/' + args.baby_id + '_scrubbed_CHNrelabel_' + judges_list_name[i] + '_1.csv')
        human = pd.DataFrame.to_numpy(human_table)
        prominence_value = human[:,2]
        len_prominence_value = len(prominence_value)
        prominence_aux = []
        if len(prominence_value) >= len(pos):
            for j in range(0, len(pos)):
                if prominence_value[j] == False or prominence_value[j] == True:
                    if prominence_value[j] == False:
                        prominence_aux.append('NOF')
                    else:
                        prominence_aux.append(lena_labels[pos[j]])
                else:
                    if prominence_value[j] > 2:
                        prominence_aux.append('NOF')
                    else:
                        prominence_aux.append(lena_labels[pos[j]])
        else:
            j = 0
            while j < len_prominence_value:
                if prominence_value[j] == False or prominence_value[j] == True:
                    if prominence_value[j] == False:
                        prominence_aux.append('NOF')
                    else:
                        prominence_aux.append(lena_labels[pos[j]])
                else:
                    if prominence_value[j] > 2:
                        prominence_aux.append('NOF')
                    else:
                        prominence_aux.append(lena_labels[pos[j]])
                j = j + 1

            while j < len(pos):
                prominence_aux.append('NOF')
                j = j + 1

        prominence.append(prominence_aux)

    # Initialize sheet
    workbook = xlsxwriter.Workbook(args.data_dir + '/' + args.baby_id + '_Qualitative_table_ALL.xlsx')
    worksheet = workbook.add_worksheet()

    # Rows and columns are zero indexed.
    row = 0
    column = 0
    # Iterating through content list
    for item in content:
        # write operation perform
        worksheet.write(row, column, item)

        # incrementing the value of row by one
        # with each iterations.
        column += 1

    # List of test number, start and end times, and lena labels
    row=1
    for item in range(0, n_test):
        worksheet.write(row, 0, item)
        worksheet.write(row, 1, n_test_start[item])
        worksheet.write(row, 2, n_test_end[item])
        worksheet.write(row, 3, lena_labels[pos[item]])

        # incrementing the value of row by one
        # with each iteratons.
        row += 1

    # List of the judgments
    column = 4
    for judge in range(0, len(judges_list_name)):
        row = 1
        for item in range(0, n_test):
            worksheet.write(row, column, prominence[judge][item])
            row += 1
        column += 1

    workbook.close()

    print('Done')

def cohen_kappa(classes, args):
    """
    Compute Cohen kappa for a given set of human judges (across and versus lena).
    """

    # Read sheet
    workbook = xlrd.open_workbook(args.data_dir + '/' + args.baby_id + '_Qualitative_table_ALL.xlsx')
    sheet = workbook.sheet_by_index(0)

    # Create judge list (column name) and values (judges)
    column_name = []
    judges = []
    for j in range(3,sheet.ncols):
        column_name.append(sheet.cell_value(0, j))
        aux = []
        for i in range(1, sheet.nrows):
            aux.append(sheet.cell_value(i, j))
        judges.append(aux)

    # Create start/end of each vocalization (to save later)
    startsec = []
    endsec = []
    for i in range(1, sheet.nrows):
        startsec.append(sheet.cell_value(i, 1))
        endsec.append(sheet.cell_value(i, 2))

    # Find the values per each class
    judges_classes = np.zeros((np.size(classes),len(judges)))
    for j in range(0, len(judges)):
        for c in range(0, np.size(classes)):
            judges_classes[c,j] = np.size(np.where(np.array(judges[j]) == classes[c]))/sheet.nrows

    # Cohen kappa
    Cohen_k = np.zeros((len(judges), len(judges)))
    for i in range(0,len(judges)):
        print(column_name[i])
        for j in range(0, len(judges)):
            Cohen_k[i,j] = sklm.cohen_kappa_score(judges[i], judges[j])

    # Initialize sheet to save Cohen kappa
    workbook = xlsxwriter.Workbook(args.data_dir + '/' + args.baby_id + '_Cohen_kappa_ALL.xlsx')
    worksheet = workbook.add_worksheet()

    # Creating content and common data
    # Define judges names on "xy axis"
    row = 0
    column = 1
    # Iterating through content list
    for item in column_name:
        # write operation perform
        worksheet.write(row, column, item)

        # incrementing the value of row by one
        # with each iterations.
        column += 1

    row = 1
    column = 0
    for item in column_name:
        # write operation perform
        worksheet.write(row, column, item)

        # incrementing the value of row by one
        # with each iterations.
        row += 1

    # Cohen k
    for row in range(1, len(column_name)+1):
        for column in range(1, len(column_name)+1):
            worksheet.write(row, column, Cohen_k[row-1,column-1])

    workbook.close()

    print('Done')

def avg_cohen(args):
    """
    Compute the average Cohen coefficients of the judges over different judgements.
    """
    # Read judge list
    #judge_list_table = pd.read_csv(args.data_dir + '/' + args.baby_id + '_judges_list.csv')
    judge_list_table = pd.read_csv(args.data_dir + '/' + 'common_judges_list.csv')
    judges_list_code = judge_list_table["judge_code"]
    judges_list_name = judge_list_table["judge_name"]

    # Read baby list
    babies_table = pd.read_csv(args.data_dir + '/' + 'babies_list.csv')
    babies = babies_table["name"]
    age = babies_table["age"]

    # Unify the data
    all_cohen = []
    for b in range(0, len(babies)):
        workbook = xlrd.open_workbook(args.data_dir + '/' + babies[b] + '_Cohen_kappa_ALL.xlsx')
        sheet = workbook.sheet_by_index(0)
        aux_cohen = np.zeros((len(judges_list_name), len(judges_list_name)))
        for i in range(1, len(judges_list_name)+1):
            for j in range(1, len(judges_list_name)+1):
                aux_cohen[i-1,j-1] = sheet.cell_value(i,j)
        all_cohen.append(aux_cohen)

    all_cohen = np.asarray(all_cohen)

    # Compute average Cohen coefficient and save the table
    avg_cohen = np.mean(all_cohen, axis=0)

    workbook = xlsxwriter.Workbook(args.data_dir + '/' + 'average_Cohen_ALL.xlsx')
    worksheet = workbook.add_worksheet()
    # Define judges names on "xy axis"
    row = 0
    column = 1
    # Iterating through content list
    for item in judges_list_name:
        # write operation perform
        worksheet.write(row, column, item)

        # incrementing the value of row by one
        # with each iterations.
        column += 1

    row = 1
    column = 0
    # Iterating through content list
    for item in judges_list_name:
        # write operation perform
        worksheet.write(row, column, item)

        # incrementing the value of row by one
        # with each iterations.
        row += 1

    for row in range(1, len(judges_list_name) + 1):
        for column in range(1, len(judges_list_name) + 1):
            worksheet.write(row, column, avg_cohen[row - 1, column - 1])

    workbook.close()

    print('Done')

if __name__ == '__main__':
    import argparse
    import glob2
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument('--option', type=str, choices=['table', 'cohen', 'avg'])
    parser.add_argument('--data_dir', type=str)
    parser.add_argument('--output_dir', type=str)
    parser.add_argument('--baby_id', type = str)
    parser.add_argument('--judge', type=str)

    args = parser.parse_args()

    if args.output_dir != None:
        if not os.path.isdir(args.data_dir + '/' + args.output_dir):
            os.makedirs(args.data_dir + '/' + args.output_dir)

    if args.option == 'table':
        qualitative_table(args)

    if args.option == 'cohen':
        classes = ['CHNNSP', 'CHNSP', 'NOF']
        cohen_kappa(classes, args)

    if args.option == 'avg':
        avg_cohen(args)

    ### Example: python3 Cohen_kappa.py --data_dir /Users/labadmin/Documents/Silvia/HumanData --option cohen --baby_id xxxx_xxxxxx