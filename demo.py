"""
本地摄像头情绪检测演示
────────────────────────────────
运行方式:  python demo.py
退出方式:  按 q 或 Esc
────────────────────────────────
"""

import cv2
from emotion.detector import create_landmarker, process_frame


def main():
    with create_landmarker() as landmarker:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ 无法打开摄像头，请检查设备连接。")
            return

        print("✅ 摄像头已启动，按 q 或 Esc 退出。")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 计算时间戳（毫秒，VIDEO 模式下必须单调递增）
            timestamp_ms = int(cv2.getTickCount() / cv2.getTickFrequency() * 1000)

            # 情绪检测
            result = process_frame(landmarker, frame, timestamp_ms)
            label = f"{result[0]} ({result[1]:.2f})" if result else "No Face Detected"

            # 绘制结果
            cv2.putText(frame, label, (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
            cv2.imshow("Emotion Demo", frame)

            # 退出检测
            if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
                break

        cap.release()
        cv2.destroyAllWindows()
        print("👋 已退出。")


if __name__ == "__main__":
    main()
