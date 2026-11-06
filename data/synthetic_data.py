import numpy as np
import matplotlib.pyplot as plt

def generate_aklo_synthetic_data(dataset_name='syn1', num_tasks=50, samples_per_task=100, seed=42):
    """
    Tạo dữ liệu giả lập (syn1, syn2, syn3, syn4) theo cấu hình trong bài báo AKLO.
    
    @Parameters:
        dataset_name (str): Tên tập dữ liệu ('syn1', 'syn2', 'syn3', 'syn4')
        num_tasks (int): Tổng số tác vụ (mặc định 50: 25 task D1, 25 task D2)
        samples_per_task (int): Số mẫu trong mỗi task (mặc định 100)
        seed (int): Seed cố định để tái lập kết quả
        
    @Return:
        tasks (list): Danh sách các dictionary chứa thông tin từng task ('task_id', 'distribution', 'X', 'y', 'a_t')
    """
    np.random.seed(seed)
    
    # Tạo chuỗi task gồm 25 task D1 và 25 task D2, sau đó xáo trộn ngẫu nhiên
    half_tasks = num_tasks // 2
    dist_sequence = ['D1'] * half_tasks + ['D2'] * (num_tasks - half_tasks)
    np.random.shuffle(dist_sequence)
    
    tasks = []
    for t_idx, dist in enumerate(dist_sequence):
        # Nhiễu epsilon_t ~ N(0, 10^-3) cho từng task
        epsilon_t = np.random.normal(0, 1e-3)
        
        if dataset_name == 'syn1':
            if dist == 'D1':
                X = np.random.multivariate_normal(mean=[10.0, 10.0], cov=np.eye(2), size=samples_per_task)
                a_t = np.array([-1.0 + epsilon_t, 1.0 + epsilon_t])
            else:  # D2
                X = np.random.multivariate_normal(mean=[20.0, 5.0], cov=np.eye(2), size=samples_per_task)
                a_t = np.array([-0.25 + epsilon_t, 1.0 + epsilon_t])
            y = np.sign(X @ a_t)
            y[y == 0] = 1.0  # Thay thế các điểm nằm trên ranh giới thành 1.0

        elif dataset_name == 'syn2':
            # Dùng chung phân bố đặc trưng X ~ N([10, 10], I)
            X = np.random.multivariate_normal(mean=[10.0, 10.0], cov=np.eye(2), size=samples_per_task)
            a_t = np.array([-1.0 + epsilon_t, 1.0 + epsilon_t])
            if dist == 'D1':
                y = np.sign(X @ a_t)
            else:  # D2 (Đối kháng)
                y = np.sign(-(X @ a_t))
            y[y == 0] = 1.0

        elif dataset_name == 'syn3':
            if dist == 'D1':
                X = np.random.multivariate_normal(mean=[10.0, 10.0], cov=np.eye(2), size=samples_per_task)
                a_t = np.array([-1.0 + epsilon_t, 1.0 + epsilon_t])
            else:  # D2
                X = np.random.multivariate_normal(mean=[20.0, 5.0], cov=np.eye(2), size=samples_per_task)
                a_t = np.array([-0.25 + epsilon_t, 1.0 + epsilon_t])
            y = X @ a_t  # Hồi quy

        elif dataset_name == 'syn4':
            X = np.random.multivariate_normal(mean=[10.0, 10.0], cov=np.eye(2), size=samples_per_task)
            a_t = np.array([-1.0 + epsilon_t, 1.0 + epsilon_t])
            if dist == 'D1':
                y = X @ a_t
            else:  # D2 (Đối kháng)
                y = -(X @ a_t)
        else:
            raise ValueError(f"dataset_name '{dataset_name}' không hợp lệ!")
            
        tasks.append({
            'task_id': t_idx + 1,
            'distribution': dist,
            'X': X,
            'y': y,
            'a_t': a_t
        })
        
    return tasks


def visualize_aklo_synthetic_data(tasks, dataset_name='syn1', cols=5):
    """
    Trực quan hóa tất cả các task dưới dạng lưới (Grid) dễ nhìn.
    
    @Parameters:
        tasks (list): Danh sách các task trả về từ hàm generate_aklo_synthetic_data.
        dataset_name (str): Tên tập dữ liệu ('syn1', 'syn2', 'syn3', 'syn4').
        cols (int): Số cột đồ thị hiển thị trên mỗi hàng (mặc định: 5).
    """
    num_tasks = len(tasks)
    rows = int(np.ceil(num_tasks / cols))  # Tự động tính số hàng
    
    # Tự động điều chỉnh kích thước hình ảnh dựa trên số lượng hàng và cột
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 3.2, rows * 3.0))
    axes = np.array(axes).reshape(-1)  # Phẳng hóa mảng axes để truy cập bằng 1 chỉ số
    
    is_classification = dataset_name in ['syn1', 'syn2']
    
    for i in range(num_tasks):
        task = tasks[i]
        ax = axes[i]
        X = task['X']
        y = task['y']
        dist = task['distribution']
        a_t = task['a_t']
        
        if is_classification:
            pos_mask = (y == 1)
            neg_mask = (y == -1)
            
            # Vẽ các điểm dữ liệu với kích thước s=15 nhỏ gọn
            ax.scatter(X[pos_mask, 0], X[pos_mask, 1], color='#1f77b4', s=15, alpha=0.6)
            ax.scatter(X[neg_mask, 0], X[neg_mask, 1], color='#d62728', s=15, alpha=0.6)
            
            # Vẽ Decision Boundary
            x1_vals = np.linspace(X[:, 0].min(), X[:, 0].max(), 50)
            if a_t[1] != 0:
                x2_vals = -(a_t[0] * x1_vals) / a_t[1]
                ax.plot(x1_vals, x2_vals, 'k--', linewidth=1.2)
        else:
            # Scatter plot cho bài toán Hồi quy
            ax.scatter(X[:, 0], X[:, 1], c=y, cmap='viridis', s=15, alpha=0.7)
            
        # Đánh dấu tiêu đề ngắn gọn
        color_title = 'darkblue' if dist == 'D1' else 'darkred'
        ax.set_title(f"T{task['task_id']} ({dist})", fontsize=10, fontweight='bold', color=color_title)
        
        # Giảm kích thước nhãn trục để không bị đè chữ
        ax.tick_params(axis='both', which='major', labelsize=8)
        ax.grid(True, linestyle=':', alpha=0.4)

    # Ẩn các ô đồ thị trống nếu tổng số task không chia hết cho số cột
    for j in range(num_tasks, len(axes)):
        fig.delaxes(axes[j])
        
    # Tạo chú thích (Legend) chung cho toàn bộ đồ thị ở phía trên
    if is_classification:
        handles = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#1f77b4', markersize=8, label='Lớp +1'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#d62728', markersize=8, label='Lớp -1'),
            plt.Line2D([0], [0], color='k', linestyle='--', linewidth=1.5, label='Boundary ($a_t^T X = 0$)')
        ]
        fig.legend(handles=handles, loc='upper center', ncol=3, bbox_to_anchor=(0.5, 1.02), fontsize=11)

    plt.suptitle(f"Trực quan hóa tập dữ liệu {dataset_name.upper()} ({num_tasks} Tasks)", y=1.05, fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()

