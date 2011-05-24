#!/usr/bin/env python

# Copyright(c)2011 @rajbot. Software license AGPL version 3.
# 
# This file is part of PycSync.
# 
#     PycSync is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     PycSync is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
# 
#     You should have received a copy of the GNU Affero General Public License
#     along with PycSync.  If not, see <http://www.gnu.org/licenses/>.
#     
#     The PycSync source is hosted at https://github.com/rajbot/PycSync

import flickrapi
import yaml
import os
import sys
import datetime
import time
import json
import hashlib

#globals
rc_path     = os.path.expanduser('~/.pycsync')
config_path = 'PycSync.yml'
meta_path   = 'PycSync_meta.yml'
lock_path   = 'PycSync.lock'

# get_config()
#______________________________________________________________________________
def get_config():

    if not os.path.exists(rc_path):
        print(".pycsync file does not exist in user homedir, exiting!")
        sys.exit(-1)
    
    if not os.path.exists(config_path):
        print("PycSync.yml file does not exist in current working directory, exiting!")
        sys.exit(-1)

    rc_dict     = yaml.load(file(rc_path))
    config_dict = yaml.load(file(config_path))
    assert 'album' in config_dict
    
    if os.path.exists(meta_path):
        meta_dict = yaml.load(file(meta_path))
    else:
        print('Creating empty meta_dict')
        meta_dict = {}
        
    return (rc_dict, config_dict, meta_dict)

# flickr_login()
#______________________________________________________________________________
def flickr_login(api_key, api_secret):
    flickr = flickrapi.FlickrAPI(api_key, api_secret)
    (token, frob) = flickr.get_token_part_one(perms='write')
    if not token: raw_input("Press ENTER after you authorized this program")
    flickr.get_token_part_two((token, frob))
    print('Flickr login complete')
    return flickr

# create_lock()
#______________________________________________________________________________
def create_lock(start_time):
    if os.path.exists(lock_path):
        print("Lock file already exists, exiting")
        sys.exit(-1)

    stream = file(lock_path, 'w')        
    yaml.dump({'start_time':start_time.isoformat()}, stream, default_flow_style=False)

# remove_lock()
#______________________________________________________________________________
def remove_lock():
    os.unlink(lock_path)

# save_meta_dict()
#______________________________________________________________________________
def save_meta_dict(meta_dict):
    stream = file(meta_path, 'w')        
    yaml.dump(meta_dict, stream, default_flow_style=False)

# flickr_upload_callback()
#______________________________________________________________________________
def flickr_upload_callback(progress, done):
    if done:
        print "  Done uploading"
    else:
        print "\b\b\b\b\b%3d%%" % progress,
        sys.stdout.flush()
        
# flickr_upload_photo()
#______________________________________________________________________________
def flickr_upload_photo(flickr, f, config_dict):
    is_public = config_dict.get('is_public', 0)
    is_family = config_dict.get('is_family', 0)
    is_friend = config_dict.get('is_friend', 0)
    
    rsp = flickr.upload(filename=f, is_public=is_public, is_family=is_family, is_friend=is_friend, format='etree', callback=flickr_upload_callback)
    photoid = rsp.findtext('photoid')

    print("  uploaded photo with id " + photoid)
    time.sleep(1)
    return photoid

# flickr_create_set()
#______________________________________________________________________________
def flickr_create_set(flickr, title, primary_photo_id):
    json_str = flickr.photosets_create(title=title, primary_photo_id=primary_photo_id, format='json', nojsoncallback=1)
    obj = json.loads(json_str)
    flickr_set_id = str(obj['photoset']['id'])
    
    print "  created set with id " + flickr_set_id
    return flickr_set_id

# get_md5
#______________________________________________________________________________
def get_md5(f):
    f = open(f)
    c = f.read()
    f.close()
    m = hashlib.md5()
    m.update(c)
    return m.hexdigest()
    
# get_meta_dict_val()
#______________________________________________________________________________
def get_meta_dict_val(f, flickr_photo_id, config_dict):
    md5 = get_md5(f)

    d = {'flickr_photo_id':flickr_photo_id, 
         'is_public':config_dict['is_public'], 
         'is_family':config_dict['is_family'], 
         'is_friend':config_dict['is_friend'],
         'md5':md5
        }
    return d

# update_dict()
#______________________________________________________________________________
def update_dict(dict, tag, val):
    needs_save = False
    
    if not tag in dict:
        print("  adding tag %s to dict with val = %s" % (tag, val))
        dict[tag] = val
        needs_save = True
    elif dict[tag] != val:
        print("  updating dict tag %s from %s to %s" % (tag, dict[tag], val))
        dict[tag] = val
        needs_save = True
        
    return needs_save

# update_meta_from_flickr()
#______________________________________________________________________________
def flickr_update_meta(flickr, f, meta_dict):
    flickr_photo_id = meta_dict[f]['flickr_photo_id']
    rsp = flickr.photos_getInfo(photo_id=flickr_photo_id, format='etree')
    import xml.etree.ElementTree as ET
    title = rsp.findtext('photo/title')    
    basename, extension = os.path.splitext(f)
    needs_save = False
    d = meta_dict[f]
    
    if title != basename:
        needs_save |= update_dict(d, 'title', title)
    
    vis = rsp.find('photo/visibility')

    is_public = int(vis.get('ispublic'))
    is_family = int(vis.get('isfamily'))
    is_friend = int(vis.get('isfriend'))    

    needs_save |= update_dict(d, 'is_public', is_public)
    needs_save |= update_dict(d, 'is_family', is_family)
    needs_save |= update_dict(d, 'is_friend', is_friend)
    
    if not 'md5' in d:
        md5 = get_md5(f)
        needs_save |= update_dict(d, 'md5', md5)
            
    if needs_save:        
        save_meta_dict(meta_dict)
        
    time.sleep(1)

# flickr_update_set()
#______________________________________________________________________________
### If this script died after an upload but before a photo was added to the set,
### add it to the set when the script is re-run
def flickr_update_set(flickr, meta_dict):
    photos_in_set = []
    flickr_set_id = meta_dict['flickr_set_id']

    for photo in flickr.walk_set(flickr_set_id):
        photos_in_set.append(photo.get('id'))
    
    for f, val in meta_dict.iteritems():
        if 'flickr_set_id' == f:
            continue

        flickr_photo_id = val['flickr_photo_id']
        if not flickr_photo_id in photos_in_set:
            print("  Adding photo %s (id=%s) to set!" % (f, flickr_photo_id))
            flickr.photosets_addPhoto(photoset_id=flickr_set_id, photo_id=flickr_photo_id)
            time.sleep(1)
            
# __main__
#______________________________________________________________________________
if '__main__' == __name__:
    (rc_dict, config_dict, meta_dict) = get_config()
    
    flickr_key    = rc_dict['flickr_api'][0]
    flickr_secret = rc_dict['flickr_api'][1]
    flickr = flickr_login(flickr_key, flickr_secret)
    
    start_time = datetime.datetime.now()
    
    create_lock(start_time)
    
    if 'flickr_set_id' in meta_dict:
        flickr_set_id = meta_dict['flickr_set_id']
    else:
        flickr_set_id = None
            
    files = os.listdir('.')
    files.sort()
    for f in files:
        print('Processing ' + f)
    
        if not os.path.isfile:
            print("  not a file, skipping")
            continue
        if not f.lower().endswith('jpg'):
            print("  filename does not end with .jpg, skipping")
            continue

        if f in meta_dict:
            print("  Already uploaded this file, checking meta")
            flickr_update_meta(flickr, f, meta_dict)
        else:
            #upload and add to set            
            flickr_photo_id = flickr_upload_photo(flickr, f, config_dict)
            meta_dict[f] = get_meta_dict_val(f, flickr_photo_id, config_dict)
            save_meta_dict(meta_dict)
    
            if None == flickr_set_id:
                #we need to upload at least one pic before creating a set
                flickr_set_id = flickr_create_set(flickr, config_dict['album'], flickr_photo_id)
                meta_dict['flickr_set_id'] = flickr_set_id
                save_meta_dict(meta_dict)
            else:
                flickr.photosets_addPhoto(photoset_id=flickr_set_id, photo_id=flickr_photo_id)

    flickr_update_set(flickr, meta_dict)
    
    remove_lock()
    end_time    = datetime.datetime.now()
    delta       = end_time - start_time
    print("Processing completed in %d days %d seconds" % (delta.days, delta.seconds))
