from app import create_app
import multiprocessing
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
app = create_app()
if __name__ == '__main__':
    workers = multiprocessing.cpu_count() * 2 + 1
    app.run(host='0.0.0.0', port=5000, threaded=True) 