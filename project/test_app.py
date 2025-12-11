# Test Application extended for loop validation
from loop_controller import run_loop

def main():
    print('Hello Sheratan')
    print('Running optional self-loop test:')
    result = run_loop(steps=1)
    print('Test loop result:', result)

if __name__ == '__main__':
    main()
