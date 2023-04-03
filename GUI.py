import gradio as gr
from json import loads
from Spider import VideoSpider
from sys import stdout

task_list=[""]
task_chatbot = [[None,None]]
task_spider = []
search_choice = ['haokan','thepaper','cctv']
choice = ['v','haokan','ku6','ifeng','thepaper','tudou','cctv']

output_file_name = "output.csv"
save_as_excel_state = True
multi_process_state = False

spider = VideoSpider()
def insert(web_id:str,video_id:str):
    global task_list,task_chatbot,task_spider
    
    if len(video_id) > 0 and len(web_id) > 0:
        if task_list[0] == "":
            task_list.pop(0)
        task_list.append(str(web_id+'_'+video_id))
        if task_chatbot[0][1] == None:
            task_chatbot.pop(0)
        task_chatbot.append([None,'web_id: '+web_id+', video_id: '+video_id])
        task_spider.append({"web_id":web_id,"video_id":video_id})
    
    return gr.Dropdown.update(choices=task_list,value=task_list[-1],label="Choose to delete"),"",task_chatbot

def delete(index):
    global task_list,task_chatbot,task_spider
    
    index = int(index)
    task_list.pop(index)
    if len(task_list) == 0:
        task_list.append("")
    task_chatbot.pop(index)
    if len(task_chatbot) == 0:
        task_chatbot.append([None,None])
    task_spider.pop(index-1)
    
    return gr.Dropdown.update(choices=task_list,value=task_list[-1],label="Choose to delete"),task_chatbot

def change_save_as_excel(state:bool):
    global save_as_excel_state
    save_as_excel_state = state
    
def change_multi_process(state:bool):
    global multi_process_state
    multi_process_state = state

def set_file_name(filename:str):
    global output_file_name
    if len(filename) != 0:
        output_file_name = filename
        
    
    return gr.Textbox.update(value="",placeholder=output_file_name)

def dict_list2list_list(dict_list):
    list_list = []
    for i in dict_list:
        list_list.append(list(i.values()))
    return list_list

def load_video_list(file):
    global task_list,task_chatbot,task_spider

    if file is not None and len(file)>0:
        json_file = loads(file)
        list_list = dict_list2list_list(json_file)
        task_spider.extend(json_file)
        if task_list[0] == "":
            task_list.pop(0)
        if task_chatbot[0][1] == None:
            task_chatbot.pop(0)
        for i in list_list:
            task_list.append(str(i[0]+'_'+i[1]))
            task_chatbot.append([None,'web_id: '+i[0]+', video_id: '+i[1]])
    
    return gr.File.update(None), gr.Dropdown.update(choices=task_list,value=task_list[-1],label="Choose to delete"),task_chatbot

def search_by_keyword(web_id,keyword):
    global task_list,task_chatbot,task_spider
    
    if len(keyword) >0 and len(web_id) > 0:
        result=spider.search_by_keyword([web_id+":"+keyword],True)
        if task_list[0] == "":
            task_list.pop(0)
        if task_chatbot[0][1] == None:
            task_chatbot.pop(0)
        for i in result:
            web_id = i[0]
            video_id = i[1]
            task_list.append(str(web_id+'_'+video_id))
            task_chatbot.append([None,'web_id: '+web_id+', video_id: '+video_id])
            task_spider.append({"web_id":web_id,"video_id":video_id})
    
    return "",gr.Dropdown.update(choices=task_list,value=task_list[-1],label="Choose to delete"),task_chatbot

def start():
    global task_spider,output_file_name,save_as_excel_state
    
    if len(task_spider) > 0:
        stdout.flush()
        print('===================== task start =========================')
        stdout.flush()
        spider.run(video_list=task_spider,
                output_file=output_file_name,
                to_excel=save_as_excel_state,
                gui_mod=True,
                multi_process=multi_process_state)
        task_list.clear()
        task_list.append("")
        task_chatbot.clear()
        task_chatbot.append([None,None])
        task_spider.clear()
        stdout.flush()
        print('===================== task end =========================')
        stdout.flush()
        return gr.Dropdown.update(choices=task_list,value=task_list[-1],label="Choose to delete"),task_chatbot
    else:
        return "",""

with gr.Blocks(theme='gstaff/sketch') as demo:
    with gr.Row():
        title = gr.Markdown("# Video Spider🐛")
    with gr.Row():
        author = gr.Markdown("👨🏻‍💻Author: Lin JiaSheng")
    with gr.Row().style(equal_height=True):
        with gr.Column(scale=3):
            with gr.Row():
                outputBot = gr.Chatbot(task_chatbot,label="Task").style(height=590)
            with gr.Row().style(equal_height=True):
                with gr.Column(min_width=100,scale=2):
                    insertDropdown = gr.Dropdown(choices=choice, value=choice[0],type="value",show_label=False).style(container=False)
                with gr.Column(scale=5):
                    insertTextbox = gr.Textbox(placeholder=f"input video id",show_label=False).style(container=False)
                with gr.Column(min_width=70,scale=1):
                    button_insert = gr.Button(label="Insert",value='Insert',variant='primary').style(size="lg")
            with gr.Row():
                with gr.Column(min_width=100,scale=2):
                    search_website_dropdown = gr.Dropdown(choices=search_choice, type="value",value = search_choice[0],show_label=False,interactive=True).style(container=False)
                with gr.Column(scale=5):
                    search_keyword = gr.Textbox(placeholder=f"input keyword",show_label=False).style(container=False)
                with gr.Column(min_width=70,scale=1):
                    button_insert_search = gr.Button(label="Search",value='Search',variant='primary')
            with gr.Row():
                button_start = gr.Button(label="Start",value='⚡ Start',variant='primary')
        with gr.Column(scale=1):
            with gr.Tab(label="Setting & Editing"):
                gr.Markdown("The file name of the exported CSV file:")
                save_file_name = gr.Textbox(label="Save as",placeholder=output_file_name)
                button_set_filename = gr.Button(label="Set filename",value='💾 Set output filename',variant='primary')

                gr.Markdown("The default output path is the output folder under the current path, and the excel file will be saved as **output.xlsx**")
                save_as_excel = gr.Checkbox(label="Save as excel?",value=True,interactive=True).style(container=True)
                multi_process = gr.Checkbox(label="Multi-process?",value=False,interactive=True).style(container=True)

                deleteDropdown = gr.Dropdown(choices=task_list, label="Choose to delete", type="index",value = task_list[-1])
                button_delete = gr.Button(label="Delete",value='❌ Delete',variant='primary')

            with gr.Tab(label="Bulk Load"):
                task_file = gr.File(label="Load Task",type="binary",file_types=[".json"])
                button_load_task = gr.Button(label="Load Task",value='📂 Load Task',variant='primary')
    
    # event
    button_insert.click(insert, 
                    inputs = [insertDropdown,insertTextbox],
                    outputs = [deleteDropdown,insertTextbox,outputBot])

    button_delete.click(delete, 
                    inputs = [deleteDropdown],
                    outputs = [deleteDropdown,outputBot])
    
    save_as_excel.change(change_save_as_excel,[save_as_excel])
    multi_process.change(change_multi_process,[multi_process])

    button_set_filename.click(set_file_name,[save_file_name],[save_file_name])
    button_load_task.click(load_video_list,[task_file],[task_file,deleteDropdown,outputBot])
    button_insert_search.click(search_by_keyword,[search_website_dropdown,search_keyword],[search_keyword,deleteDropdown,outputBot])
    button_start.click(start,[],[deleteDropdown,outputBot])

#print("请访问 http://localhost:12345 或你指定的端口")

demo.title="Video Spider🐛"