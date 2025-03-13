import time
import threading
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import ImageTask, TaskStatus
from converter import process_image
from config import DATABASE_URL, POLL_INTERVAL, WORKER_THREADS


class ConversionWorker:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        self.running = False
        self.thread = None
    
    def reset_unfinished_tasks(self):
        """将所有未完成任务状态重置为 PENDING"""
        session = self.Session()
        try:
            # 找到所有 CONVERTING 状态的任务并重置为 PENDING
            unfinished_tasks = session.query(ImageTask).filter_by(status=TaskStatus.CONVERTING).all()
            for task in unfinished_tasks:
                task.status = TaskStatus.PENDING
            session.commit()
            print(f"Reset {len(unfinished_tasks)} unfinished tasks to PENDING status")
        except Exception as e:
            print(f"Error resetting unfinished tasks: {str(e)}")
            session.rollback()
        finally:
            session.close()
    
    def start(self):
        """启动工作线程"""
        print("Starting worker")
        # 先重置未完成的任务
        self.reset_unfinished_tasks()
        
        if self.thread is not None and self.thread.is_alive():
            return
        self.running = True
        self.thread = threading.Thread(target=self._work_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """停止工作线程"""
        self.running = False
        if self.thread is not None:
            self.thread.join()
    
    def _work_loop(self):
        """工作线程主循环"""
        while self.running:
            session = self.Session()
            try:
                # 悲观锁获取一个待处理任务
                task = session.query(ImageTask).filter_by(
                    status=TaskStatus.PENDING
                ).with_for_update(skip_locked=True).first()
                
                if task is None:
                    session.commit()
                    time.sleep(POLL_INTERVAL)
                    continue
                
                # 更新状态为转换中
                task.status = TaskStatus.CONVERTING
                session.commit()
                
                try:
                    # 进行图片转换
                    result_path, original_filename = process_image(task.original_url, task.format, task.id)
                    
                    # 更新任务状态为成功，同时保存原始文件名
                    task.result_path = result_path
                    task.original_filename = original_filename
                    task.status = TaskStatus.SUCCEED
                    session.commit()
                except Exception as e:
                    print(f"Error converting image {task.id}: {str(e)}")
                    task.status = TaskStatus.FAILED
                    session.commit()
                
            except Exception as e:
                print(f"Worker error: {str(e)}")
                session.rollback()
            finally:
                session.close()
                time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    import multiprocessing

    def run_worker():
        worker = ConversionWorker()
        # Reset unfinished tasks before starting work loop
        worker.reset_unfinished_tasks()
        worker.running = True
        worker._work_loop()

    processes = []
    for _ in range(WORKER_THREADS):
        p = multiprocessing.Process(target=run_worker)
        p.start()
        processes.append(p)

    for p in processes:
        p.join()