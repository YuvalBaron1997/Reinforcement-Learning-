#1.יבוא
import tkinter as tk
import random
import time

# ייבוא הרובוט (נוודא שהקובץ agent.py נמצא באותה תיקייה)
try:
    from agent import QLearningRobot
    ROBOT_AVAILABLE = True
    print("✅ רובוט Q-Learning נטען בהצלחה!")
except ImportError:
    ROBOT_AVAILABLE = False
    print("⚠️ לא נמצא קובץ agent.py - הסביבה תעבוד בלי רובוט")


#2. יצירת החתול
class Cat:
    """מחלקת חתול - מכשול דינמי"""
    def __init__(self, x, y, canvas, cell_size):
        self.x = x
        self.y = y
        self.canvas = canvas
        self.cell_size = cell_size
        self.direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        
        # יצירת החתול על הקנבס
        self.cat_id = self.canvas.create_oval(
            x * cell_size + 5, y * cell_size + 5,
            (x + 1) * cell_size - 5, (y + 1) * cell_size - 5,
            fill="orange", outline="red", width=2
        )
    
    def move(self, environment):
        """הזזת החתול"""
        # חישוב מיקום חדש - לפי הכיוון
        new_x = self.x + self.direction[0]
        new_y = self.y + self.direction[1]
        
        # בדיקת גבולות
        if (new_x < 0 or new_x >= environment.total_width or 
            new_y < 0 or new_y >= environment.total_height):
            # שינוי כיוון כשפוגע בקיר
            self.direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        else:
            # תנועה רגילה
            old_x, old_y = self.x, self.y
            self.x, self.y = new_x, new_y
            
            # עדכון המיקום על הקנבס
            dx = (new_x - old_x) * self.cell_size
            dy = (new_y - old_y) * self.cell_size
            self.canvas.move(self.cat_id, dx, dy)
        
        # שינוי כיוון אקראי (20% סיכוי)
        if random.random() < 0.2:
            self.direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
    
    def get_position(self):
        return (self.x, self.y)


class IRobotEnvironment:
    """סביבת המשחק עם tkinter"""
    
    def __init__(self, num_cats=3, num_dirt=8, use_robot=True):
        # הגדרות הסביבה
        self.living_room_size = 10  # סלון 10x10
        self.kitchen_size = 10      # מטבח 10x10
        self.total_width = 20       # רוחב כולל
        self.total_height = 10      # גובה כולל
        self.cell_size = 30         # גודל כל תא בפיקסלים
        
        # הגדרות משחק
        self.num_cats = num_cats
        self.num_dirt = num_dirt
        self.cats = []
        self.dirt_positions = set()
        
        # הגדרות רובוט
        self.use_robot = use_robot and ROBOT_AVAILABLE
        self.robot = None
        self.robot_id = None  # מזהה הרובוט על הקנבס
        
        # הגדרות חלון
        self.window = tk.Tk()
        self.window.title("🤖 iRobot & Cats Environment")
        self.window.geometry("800x450")  # הגדלנו קצת בגלל כפתורים נוספים
        
        # יצירת הקנבס
        canvas_width = self.total_width * self.cell_size
        canvas_height = self.total_height * self.cell_size
        
        self.canvas = tk.Canvas(
            self.window, 
            width=canvas_width, 
            height=canvas_height,
            bg="lightblue"
        )
        self.canvas.pack(pady=10)
        
        # יצירת פאנל מידע
        self.info_frame = tk.Frame(self.window)
        self.info_frame.pack()
        
        self.info_label = tk.Label(
            self.info_frame, 
            text="מכין סביבה...", 
            font=("Arial", 12)
        )
        self.info_label.pack()
        
        # יצירת רובוט אם זמין
        if self.use_robot:
            self.robot = QLearningRobot(learning_rate=0.1, discount_factor=0.9, epsilon=0.3)
            print("🤖 רובוט נוצר והוכנס לסביבה!")
        
        # כפתורי בקרה
        self.create_control_buttons()
        
        self.is_running = False
        
        # אתחול הסביבה
        self.setup_environment()
        self.reset()
        
    def create_control_buttons(self):
        """יצירת כפתורי בקרה"""
        control_frame = tk.Frame(self.window)
        control_frame.pack(pady=5)
        
        # שורה ראשונה - בקרות בסיסיות
        row1 = tk.Frame(control_frame)
        row1.pack()
        
        tk.Button(row1, text="איפוס", command=self.reset, 
                 font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(row1, text="חתולים התחל/עצור", command=self.toggle_animation, 
                 font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        # שורה שנייה - בקרות רובוט (אם זמין)
        if self.use_robot:
            row2 = tk.Frame(control_frame)
            row2.pack(pady=5)
            
            tk.Button(row2, text="רובוט - צעד אחד", command=self.robot_single_step, 
                     font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
            tk.Button(row2, text="רובוט - 10 צעדים", command=self.robot_multiple_steps, 
                     font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
    def setup_environment(self):
        """יצירת הרקע והרשת"""
        # מחיקת הכל
        self.canvas.delete("background")
        
        # ציור רקע לחדרים
        # סלון (0-9)
        self.canvas.create_rectangle(
            0, 0, 
            self.living_room_size * self.cell_size, 
            self.total_height * self.cell_size,
            fill="lightblue", outline="blue", width=2, tags="background"
        )
        
        # מטבח (10-19)
        self.canvas.create_rectangle(
            self.living_room_size * self.cell_size, 0,
            self.total_width * self.cell_size, 
            self.total_height * self.cell_size,
            fill="lightgreen", outline="green", width=2, tags="background"
        )
        
        # כותרות חדרים
        self.canvas.create_text(
            self.living_room_size * self.cell_size // 2, 15,
            text="סלון", font=("Arial", 14, "bold"), tags="background"
        )
        
        self.canvas.create_text(
            (self.living_room_size + self.kitchen_size // 2) * self.cell_size, 15,
            text="מטבח", font=("Arial", 14, "bold"), tags="background"
        )
        
        # רשת
        for i in range(self.total_width + 1):
            x = i * self.cell_size
            self.canvas.create_line(
                x, 0, x, self.total_height * self.cell_size,
                fill="gray", width=1, tags="background"
            )
        
        for i in range(self.total_height + 1):
            y = i * self.cell_size
            self.canvas.create_line(
                0, y, self.total_width * self.cell_size, y,
                fill="gray", width=1, tags="background"
            )
        
        # עמדת טעינה
        self.canvas.create_rectangle(
            self.cell_size + 5, self.cell_size + 5,
            2 * self.cell_size - 5, 2 * self.cell_size - 5,
            fill="yellow", outline="orange", width=3, tags="background"
        )
        self.canvas.create_text(
            1.5 * self.cell_size, 1.5 * self.cell_size,
            text="🔋", font=("Arial", 16), tags="background"
        )
    
    def reset(self):
        """איפוס הסביבה"""
        # עצירת האנימציה
        self.is_running = False
        
        # מחיקת חתולים ישנים מהקנבס
        for cat in self.cats:
            self.canvas.delete(cat.cat_id)
        
        # מחיקת רובוט ישן מהקנבס
        if self.robot_id:
            self.canvas.delete(self.robot_id)
            self.robot_id = None
        
        # מחיקת אלמנטים ישנים
        self.canvas.delete("dirt")
        self.canvas.delete("cat")
        self.canvas.delete("robot")
        
        # איפוס הרובוט
        if self.robot:
            self.robot.reset()
        
        # יצירת ליכלוכים במטבח
        self.dirt_positions = set()
        self.dirt_objects = {}
        
        while len(self.dirt_positions) < self.num_dirt:
            x = random.randint(10, 19)  # רק במטבח
            y = random.randint(0, 9)
            if (x, y) not in self.dirt_positions:
                self.dirt_positions.add((x, y))
                
                # יצירת ליכלוך על הקנבס
                dirt_id = self.canvas.create_oval(
                    x * self.cell_size + 8, y * self.cell_size + 8,
                    (x + 1) * self.cell_size - 8, (y + 1) * self.cell_size - 8,
                    fill="brown", outline="black", width=2, tags="dirt"
                )
                self.dirt_objects[(x, y)] = dirt_id
        
        # יצירת חתולים
        self.cats = []
        for i in range(self.num_cats):
            while True:
                x = random.randint(0, 19)
                y = random.randint(0, 9)
                # ודא שהחתול לא על עמדת טעינה או ליכלוך
                if (x, y) != (1, 1) and (x, y) not in self.dirt_positions:
                    cat = Cat(x, y, self.canvas, self.cell_size)
                    self.cats.append(cat)
                    break
        
        # יצירת הרובוט על הקנבס
        if self.robot:
            self.create_robot_on_canvas()
        
        # עדכון מידע
        self.update_info()
    
    def update_info(self):
        print(f"סביבה אותחלה: {len(self.dirt_positions)} ליכלוכים, {len(self.cats)} חתולים")
        if self.robot:
            print(f"רובוט במיקום: {self.robot.get_position()}")
    
    def create_robot_on_canvas(self):
        """יצירת הרובוט על הקנבס"""
        if not self.robot:
            return
            
        robot_x, robot_y = self.robot.get_position()
        
        # צבע הרובוט לפי מצב
        if self.robot.is_charging:
            robot_color = "yellow"
        else:
            robot_color = "blue"
        
        # יצירת ריבוע לרובוט
        self.robot_id = self.canvas.create_rectangle(
            robot_x * self.cell_size + 3, robot_y * self.cell_size + 3,
            (robot_x + 1) * self.cell_size - 3, (robot_y + 1) * self.cell_size - 3,
            fill=robot_color, outline="darkblue", width=3, tags="robot"
        )
    
    def update_robot_on_canvas(self):
        """עדכון מיקום הרובוט על הקנבס"""
        if not self.robot or not self.robot_id:
            return
        
        robot_x, robot_y = self.robot.get_position()
        
        # עדכון מיקום
        self.canvas.coords(
            self.robot_id,
            robot_x * self.cell_size + 3, robot_y * self.cell_size + 3,
            (robot_x + 1) * self.cell_size - 3, (robot_y + 1) * self.cell_size - 3
        )
        
        # עדכון צבע לפי מצב
        if self.robot.is_charging:
            self.canvas.itemconfig(self.robot_id, fill="yellow")
        else:
            self.canvas.itemconfig(self.robot_id, fill="blue")
    
    def collect_dirt_if_present(self):
        """בדיקה ואיסוף ליכלוך אם הרובוט עליו"""
        if not self.robot:
            return False
            
        robot_pos = self.robot.get_position()
        
        if robot_pos in self.dirt_positions:
            # הסרת הליכלוך
            self.dirt_positions.remove(robot_pos)
            
            # הסרה מהקנבס
            dirt_id = self.dirt_objects.get(robot_pos)
            if dirt_id:
                self.canvas.delete(dirt_id)
                del self.dirt_objects[robot_pos]
            
            print(f"🧹 ליכלוך נאסף ב-{robot_pos}! נותרו {len(self.dirt_positions)}")
            return True
        
        return False
    
    def robot_single_step(self):
        """ביצוע צעד אחד של הרובוט"""
        if not self.robot:
            return
        
        # קבלת מיקומי חתולים ליכלוכים
        cats_positions = [cat.get_position() for cat in self.cats]
        
        # ביצוע צעד של הרובוט
        reward, done = self.robot.step(cats_positions, self.dirt_positions.copy())
        
        # בדיקת איסוף ליכלוך
        dirt_collected = self.collect_dirt_if_present()
        
        # עדכון הרובוט על הקנבס
        self.update_robot_on_canvas()
        
        # עדכון מידע
        self.update_info()
        
        print(f"🤖 צעד רובוט: מיקום {self.robot.get_position()}, תגמול: {reward}")
        
        if done:
            print("🎉 המשימה הושלמה!")
    
    def robot_multiple_steps(self):
        """ביצוע מספר צעדים של הרובוט"""
        if not self.robot:
            return
            
        for step in range(10):
            if len(self.dirt_positions) == 0:
                print("🎉 כל הליכלוכים נאספו!")
                break
                
            cats_positions = [cat.get_position() for cat in self.cats]
            reward, done = self.robot.step(cats_positions, self.dirt_positions.copy())
            
            self.collect_dirt_if_present()
            self.update_robot_on_canvas()
            
            if done:
                print("🎉 המשימה הושלמה!")
                break
            
            # הזזת חתולים בכל צעד
            self.move_cats()
            
            # עיכוב קטן לראות את התנועה
            self.window.update()
            time.sleep(0.1)
        
        self.update_info()
    
    def toggle_learning_mode(self):
        """הפעלה/כיבוי מצב למידה"""
        if not self.robot:
            return
            
        self.robot_learning_mode = not self.robot_learning_mode
        
        if self.robot_learning_mode:
            print("🧠 מצב למידה הופעל - הרובוט ילמד בזמן אמת!")
            self.learning_loop()
        else:
            print("⏸️ מצב למידה נעצר")
    
    def learning_loop(self):
        """לולאת למידה של הרובוט"""
        if not self.robot_learning_mode or not self.robot:
            return
        
        # צעד של רובוט
        cats_positions = [cat.get_position() for cat in self.cats]
        reward, done = self.robot.step(cats_positions, self.dirt_positions.copy())
        
        self.collect_dirt_if_present()
        self.update_robot_on_canvas()
        
        # תנועת חתולים
        self.move_cats()
        
        if done:
            print("🎉 אפיזוד הושלם! מתחיל אפיזוד חדש...")
            self.reset()
        
        # המשך הלולאה
        if self.robot_learning_mode:
            self.window.after(200, self.learning_loop)  # חזרה אחרי 200ms
    
    def update_info(self):
        """עדכון פאנל המידע"""
        cats_pos = [cat.get_position() for cat in self.cats]
        info_text = f"ליכלוכים: {len(self.dirt_positions)} | חתולים: {len(self.cats)}"
        
        if self.robot:
            robot_pos = self.robot.get_position()
            collisions = self.robot.collision_count
            charging = "🔋" if self.robot.is_charging else "🤖"
            info_text += f" | רובוט: {robot_pos} {charging} | התנגשויות: {collisions}/3"
        
        self.info_label.config(text=info_text)
    
    def move_cats(self):
        """הזזת כל החתולים"""
        for cat in self.cats:
            cat.move(self)
        self.update_info()
    
    def toggle_animation(self):
        """הפעלה/עצירה של אנימציית החתולים"""
        self.is_running = not self.is_running
        if self.is_running:
            self.animate()
    
    def animate(self):
        """לולאת אנימציית החתולים"""
        if self.is_running:
            self.move_cats()
            # חזרה על האנימציה אחרי 500 מילישניות
            self.window.after(500, self.animate)
    
    def get_current_state(self):
        """החזרת מצב הסביבה הנוכחי (לשימוש חיצוני)"""
        return {
            'robot_position': self.robot.get_position() if self.robot else None,
            'cats_positions': [cat.get_position() for cat in self.cats],
            'dirt_positions': self.dirt_positions.copy(),
            'game_over': len(self.dirt_positions) == 0
        }
    
    def run(self):
        """הפעלת הסימולציה"""
        print("🤖 מתחיל סימולציה...")
        if self.robot:
            print("🎮 כפתורי רובוט זמינים:")
            print("  - צעד אחד: צעד בודד")
            print("  - 10 צעדים: ריצה מהירה")
            print("  - מצב למידה: למידה רציפה")
        print("🐱 לחץ על 'חתולים התחל/עצור' כדי להפעיל תנועת החתולים")
        self.window.mainloop()


# פונקציות להרצה
def run_simulation_with_robot():
    """הרצת הסימולציה עם רובוט"""
    env = IRobotEnvironment(num_cats=2, num_dirt=6, use_robot=True)
    env.run()

def run_simulation_without_robot():
    """הרצת הסימולציה בלי רובוט (רק חתולים)"""
    env = IRobotEnvironment(num_cats=2, num_dirt=8, use_robot=False)
    env.run()

# הרצה ישירה
if __name__ == "__main__":
    print("🤖 iRobot & Cats Environment with Q-Learning Robot!")
    print("=" * 55)
    
    if ROBOT_AVAILABLE:
        run_simulation_with_robot()
    else:
        print("💭 מריץ רק עם חתולים...")
        run_simulation_without_robot()
