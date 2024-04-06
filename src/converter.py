import os
import sys
import yaml
import json
import shutil
import random
import argparse
import numpy as np
import pandas as pd


class DatasetConverter:
    def __init__(self):
        argparser = argparse.ArgumentParser(description="Dataset Converter")
        argparser.add_argument('--format', '-f', help='Specify the conversion format', default='sly')
        argparser.add_argument('--dir', '-d', help='Specify the directory of the dataset to convert', default=os.path.join(os.getcwd(), 'dataset'))
        argparser.add_argument('--inplace', '-ip', help='Overwrite the dataset or convert it into another folder', action='store_true')

        # Parse command-line arguments
        args = argparser.parse_args()

        # ensure directory being OpenAcces_RGBD_apple_dataset
        if os.getcwd().endswith(('src')):
            os.chdir('..')

        #  Access the value of --format argument
        if args.format:
            print("Format specified:", args.format)
        else:
            print("No format specified")

        if bool(args.inplace) == True:
                response = ''
                while response.lower() not in ['y', 'n']:
                    response = input('\n[WARNING] Are you sure you want to overwrite the dataset? Images and labels will be LOST [n/y]: ')
                    if response.lower() == 'y':
                        self.conversion_dir = os.path.join(os.getcwd(), args.dir)
                        break
                    elif response.lower() == 'n':
                        self.conversion_dir = os.path.join(os.getcwd(), f'{args.dir}_{args.format.upper()}')
                        break
                    else:
                        continue

        else:
            self.conversion_dir = os.path.join(os.getcwd(), f'{args.dir}_{args.format.upper()}')

        print(f'Converted dataset is being saved to: {self.conversion_dir}')

        # to host datset info
        self.unique_class_titles = []
        self.unique_ref_obj = []
                
        if args.format.lower() == 'sly':
            print('[CONVERSION] ...dataset to supervisely')
            
            self.img_dir = os.path.join(self.conversion_dir, 'img')
            self.annotation_dir = os.path.join(self.conversion_dir, 'ann')
            os.makedirs(self.img_dir, exist_ok=True)
            os.makedirs(self.annotation_dir, exist_ok=True)

            # generate meta.json and save it in self.conversion_dir
            self.meta_json = {"classes": [], "tags": [], "projectType": "images"}
            self.proj_annot_dict = {}

            for cam_obj_distance in os.listdir(args.dir):
                for point_of_view in os.listdir(os.path.join(args.dir, f'{cam_obj_distance}')):
                    for date in os.listdir(os.path.join(args.dir, f'{cam_obj_distance}/{point_of_view}')):
                        for file in os.listdir(os.path.join(args.dir, f'{cam_obj_distance}/{point_of_view}/{date}')):
                            if file.endswith('.png'):
                                fn = os.path.join(args.dir, f'{cam_obj_distance}/{point_of_view}/{date}/{file}') 
                                # modify the name because when importing in sypervisely files `P*.*` will be overwritten
                                new_fn = os.path.join(self.img_dir, f'{date}#{cam_obj_distance}#{point_of_view}#{file}')
                              
                                # clone file into proper folder
                                shutil.copyfile(fn, new_fn)

                                if args.inplace:
                                    os.remove(fn)
                            
                            elif file.endswith('.json'):
                                fn = os.path.join(args.dir, f'{cam_obj_distance}/{point_of_view}/{date}/{file}') 
                                # modify the name because when importing in sypervisely files `P*.*` will be overwritten
                                new_fn = os.path.join(self.annotation_dir, f'{date}#{cam_obj_distance}#{point_of_view}#{file}')

                                # clone file into proper folder
                                shutil.copyfile(fn, new_fn)

                                # read annotation file to compile the meta.json
                                with open(fn) as json_file:
                                    annot = json.load(json_file)
                                
                                for obj in annot['objects']:
                                    self.proj_annot_dict[obj['classTitle']] = (obj['classId'], obj['labelerLogin'])

                                    self.unique_class_titles.append(obj['classTitle'])
                                    if obj['description'] != '':
                                        self.unique_ref_obj.append(obj['description'])
                                
                                if args.inplace:
                                    os.remove(fn)
            
            for class_title, class_info in self.proj_annot_dict.items():
                # random color assignment for labelling tool
                red = random.randint(0, 255)
                green = random.randint(0, 255)
                blue = random.randint(0, 255)
                # Convert the decimal values to hexadecimal and format them appropriately
                color_hex = "#{:02X}{:02X}{:02X}".format(red, green, blue)

                self.meta_json["classes"].append({
                                        "title": class_title,
                                        "description": class_info[1],
                                        "shape": "rectangle",
                                        "color":color_hex,
                                        "geometry_config": {},
                                        "id": class_info[0],
                                        "hotkey": "" })
            
            # save meta.json
            meta_json_file = os.path.join(self.conversion_dir, "meta.json")
            with open(meta_json_file, 'w') as outfile:
                json.dump(self.meta_json, outfile, indent=len(self.meta_json.keys()))
            outfile.close()


        elif args.format.lower() == 'yolo':
            print('[CONVERSION] ... to YOLO')

            # steps to accomplish:
            # process images
            # process labels
            # generate the dataset.yaml

            dataset_yaml = {'path': '.',
                            'train': 'images/train',
                            'val': 'images/val',
                            'nc': 0,
                            'names' : {}}
                        
            self.img_dir = os.path.join(self.conversion_dir, 'images/train')
            self.annotation_dir = os.path.join(self.conversion_dir, 'labels/train')
            # generate folders
            os.makedirs(self.img_dir, exist_ok=True)
            os.makedirs(os.path.join(self.conversion_dir, 'images/val'), exist_ok=True)
            os.makedirs(self.annotation_dir, exist_ok=True)
            os.makedirs(os.path.join(self.conversion_dir, 'labels/val'), exist_ok=True)

            # process the dataset
            for cam_obj_distance in os.listdir(args.dir):
                for point_of_view in os.listdir(os.path.join(args.dir, f'{cam_obj_distance}')):
                    for date in os.listdir(os.path.join(args.dir, f'{cam_obj_distance}/{point_of_view}')):
                        for file in os.listdir(os.path.join(args.dir, f'{cam_obj_distance}/{point_of_view}/{date}')):
                            if file.endswith('.png'):
                                fn = os.path.join(args.dir, f'{cam_obj_distance}/{point_of_view}/{date}/{file}') 
                                # modify the name because when importing in sypervisely files `P*.*` will be overwritten
                                new_fn = os.path.join(self.img_dir, f'{date}#{cam_obj_distance}#{point_of_view}#{file}')
                              
                                # clone file into proper folder
                                shutil.copyfile(fn, new_fn)

                                if args.inplace:
                                    os.remove(fn)
                            
                            elif file.endswith('.json'):
                                fn = os.path.join(args.dir, f'{cam_obj_distance}/{point_of_view}/{date}/{file}') 
                               
                                # read annotation file to compile the meta.json
                                with open(fn) as json_file:
                                    annot = json.load(json_file)

                                # init the label.txt and modify the name, otherwise files `P*.*` will be overwritten
                                new_fn = os.path.join(self.annotation_dir, f'{date}#{cam_obj_distance}#{point_of_view}#{file.replace("json", "txt")}')
                                txt = pd.DataFrame(columns=['cls', 'x', 'y', 'w', 'h'])

                                # populate the label
                                for obj_index, obj in enumerate(annot['objects']):
                                    # add firts class
                                    if len(dataset_yaml['names']) == 0:
                                        dataset_yaml['names'][len(dataset_yaml['names'])] = obj['classTitle']
                                        dataset_yaml['nc'] += 1
                                    # if class not in yaml, add it
                                    if obj['classTitle'] not in  dataset_yaml['names'].values():
                                        dataset_yaml['names'][len(dataset_yaml['names'])] = obj['classTitle']
                                        dataset_yaml['nc'] += 1


                                    self.unique_class_titles.append(obj['classTitle'])

                                    # to normalized obj coords
                                    W = annot['size']['width']
                                    H = annot['size']['height']

                                    # i need cls_index, x, y, w, h
                                    x, y, w, h = 0, 0, 0, 0

                                    # get class id
                                    class_names= list(dataset_yaml['names'].values())
                                    if str(obj['classTitle']) in class_names:
                                        cls_id = np.array(class_names.index(obj['classTitle']), dtype='int')
                                    
                                        # normalize coords
                                        tl, br = obj['points']['exterior'][0], obj['points']['exterior'][1]
                                        x = (tl[0] + (br[0] - tl[0]) / 2 ) / W
                                        y = (tl[1] + (br[1] - tl[1]) / 2 ) / H
                                        w = (br[0] - tl[0]) / W
                                        h = (br[1] - tl[1]) / H

                                        # add data to the label
                                        txt.loc[obj_index] = ([cls_id, x, y, w, h ])

                                        self.unique_ref_obj.append(obj['description'])

                                # save label
                                txt.to_csv(os.path.join(self.annotation_dir, new_fn), index=False, header=False)

                                
                                if args.inplace:
                                    os.remove(fn)
            
            print(dataset_yaml)

            # save dataset_yaml
            with open(os.path.join(self.conversion_dir, 'dataset.yaml'), 'w') as outfile:
                yaml.dump(dataset_yaml, outfile, sort_keys=False)

            # copy images in train folder



            # convert labels into yolo detection format




        print(f'\nDataset converted inside {self.conversion_dir}\n   UNIQUE CLASSES: {sorted(set(self.unique_class_titles), reverse=True)}\n   REFERENCE OBJECTS: {sorted(set(self.unique_ref_obj), reverse=True)}')


            



if __name__ == '__main__':
    
    DatasetConverter()