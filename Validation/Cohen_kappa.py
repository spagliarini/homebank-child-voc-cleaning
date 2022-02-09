#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: silviapagliarini
"""
import os
import sklearn
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
    judge_list_table = pd.read_csv(args.data_dir + '/' + args.baby_id + '_judges_list.csv')
    judges_list_code = judge_list_table["judge_code"]
    judges_list_name = judge_list_table["judge_name"]

    # Initialize sheet
    workbook = xlsxwriter.Workbook(args.data_dir + '/' + args.baby_id + '_Qualitative_table.xlsx')
    worksheet = workbook.add_worksheet()

    n_test_table = pd.read_csv(args.data_dir + '/' + args.baby_id + '_scrubbed_CHNrelabel_' + judges_list_name[0] + '_1.csv')
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
        prominence_aux = []
        for j in range(0, len(pos)):
            if prominence_value[j] > 2:
                prominence_aux.append('NOF')
            else:
                prominence_aux.append(lena_labels[pos[j]])
        prominence.append(prominence_aux)

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
    workbook = xlrd.open_workbook(args.data_dir + '/' + args.baby_id + '_Qualitative_table.xlsx')
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
            Cohen_k[i,j] = sklearn.metrics.cohen_kappa_score(judges[i], judges[j])

    # Initialize sheet to save Cohen kappa
    workbook = xlsxwriter.Workbook(args.data_dir + '/' + args.baby_id + '_Cohen_kappa.xlsx')
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

if __name__ == '__main__':
    import argparse
    import glob2
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument('--option', type=str, choices=['table', 'cohen'])
    parser.add_argument('--data_dir', type=str)
    parser.add_argument('--output_dir', type=str)
    parser.add_argument('--baby_id', type = str)

    args = parser.parse_args()

    if args.output_dir != None:
        if not os.path.isdir(args.data_dir + '/' + args.output_dir):
            os.makedirs(args.data_dir + '/' + args.output_dir)

    if args.option == 'table':
        qualitative_table(args)

    if args.option == 'cohen':
        classes = ['CHNNSP', 'CHNSP', 'NOF']
        cohen_kappa(classes, args)

    ### Example: python3 Cohen_kappa.py --data_dir /Users/labadmin/Documents/Silvia/HumanData --option cohen --baby_id xxxx_xxxxxx