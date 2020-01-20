class agent(object):

	def __init__(self,name='agent'):
		self.name = name

	def hello(self,msg='Hello world'):
		print(msg)

	if __name__ == '__main__':
  		main1 = agent()
  		main1.hello()
