import sys
from GUI import demo,spider
from getopt import getopt,GetoptError

if __name__ == '__main__':
    print("start task")
    argv = sys.argv[1:]
    task_file = './config/VideoList.json'
    output_file = 'output.csv'
    output_dir = './output'
    to_excel = False
    gui_mod = False
    search_mod = False
    search_keywords = ''
    multi_process = False
    port = int(12345)
    
    # 读取命令行参数
    print('prase argv...')
    if len(argv) > 0:
        try:
            opts, args = getopt(argv,"t:c:o:d:s:p:emg",["task=","config=","output=","dir=","search=","multi_process","gui","port="])
        except GetoptError:
            raise GetoptError('req.py -t/--task <task> -e -o/--output <output> -d/--dir <dir> -s/--search <web_id>:<keyword>_<web_id>:<keyword>... -m/--multi_process -g/--gui -p/--port <port>')
        for opt, arg in opts:
            if opt in ("-t", "--task"):
                task_file = arg
            elif opt in ("-o", "--ofile"):
                output_file = arg
            elif opt in ("-d", "--dir"):
                output_dir = arg
            elif opt in ("-s","--search"):
                search_mod = True
                search_keywords = arg
            elif opt in ("-e"):
                to_excel = True
            elif opt in ("-m","--multi_process"):
                multi_process = True
            elif opt in ("-g","--gui"):
                gui_mod = True
            elif opt in ("-p","--port"):
                port = int(arg)
    
    if(gui_mod):
        demo.launch(server_port=port,favicon_path="./assets/favicon.ico",inbrowser=True)
    else:
        spider.run(task_file,output_file,output_dir,[],to_excel,gui_mod,search_mod,search_keywords,multi_process)
