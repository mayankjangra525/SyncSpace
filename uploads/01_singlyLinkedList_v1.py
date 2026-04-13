class Node:
    def __init__(self,info,next=None):
        self.next=next
        self.info=info
class singylinkedList:
    def __init__(self):
        self.head=None
    def insertAtEnd(self,value):
        temp=Node(value)
        t1=self.head
        if(self.head):
            while (t1.next):
                t1=t1.next
            t1.next=temp
        else:
            self.head=temp
    def insertAtBeg(self,value):
        temp=Node(value)
        temp.next=self.head
        self.head=temp
    def insertInMid(self, value, x):
        temp = Node(value)
        t1 = self.head

        while t1:
            if t1.info == x:
              temp.next = t1.next
              t1.next = temp
              return   # 🔥 stop after first insert
            t1 = t1.next
                

    def PrintLL(self):
        t1=self.head
        while (t1):
            print(t1.info,end="->")
            t1=t1.next
        print(None)
       
obj=singylinkedList()
obj.insertAtEnd(90)
obj.insertAtEnd(90)
obj.insertAtEnd(90)
obj.insertAtEnd(90)
obj.insertAtBeg(13)
obj.insertInMid(20,90)
obj.PrintLL()